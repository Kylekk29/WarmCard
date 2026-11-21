import atexit
import contextlib
import importlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


class WarmCardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = cls.enterClassContext(tempfile.TemporaryDirectory())
        cls.enterClassContext(patch.dict(os.environ, {
            "WARMCARD_LOG_DIR": directory,
            "AI_API_KEY": "test-key",
        }))
        with patch("openai.OpenAI"), contextlib.redirect_stdout(io.StringIO()):
            cls.service = importlib.import_module("app")
        cls.addClassCleanup(atexit.unregister, cls.service.shutdown)
        for handler in cls.service.log.handlers[:]:
            cls.addClassCleanup(handler.close)
            cls.addClassCleanup(cls.service.log.removeHandler, handler)
        cls.store = Path(cls.service.share_store_file)

    def setUp(self):
        self.store.unlink(missing_ok=True)
        self.client = self.service.app.test_client()

    def test_studio_and_recipient_page(self):
        studio = self.client.get("/")
        self.addCleanup(studio.close)
        self.assertEqual(studio.status_code, 200)
        self.assertIn(b"Greeting Card Studio", studio.data)

        created = self.client.post("/api/share", json={
            "name": "Alice",
            "occasion": "birthday",
            "message": "Happy birthday!\n<script>alert(1)</script>",
        })
        self.assertEqual(created.status_code, 200)
        share = created.get_json()
        saved = json.loads(self.store.read_text(encoding="utf-8"))
        self.assertEqual(saved[share["share_id"]], share["share_data"])

        page = self.client.get(share["url"])
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.headers["Cache-Control"], "no-store")
        self.assertIn("noindex", page.headers["X-Robots-Tag"])
        self.assertIn(b"For Alice", page.data)
        self.assertIn(b"Happy birthday!\n&lt;script&gt;alert(1)&lt;/script&gt;", page.data)
        self.assertNotIn(b"<script>", page.data)

        api = self.client.get(f"/api/share/{share['share_id']}")
        self.assertEqual(api.get_json()["theme"]["label"], "Birthday")

    def test_existing_share_and_missing_link(self):
        share_id = "12345678-abc"
        self.store.write_text(json.dumps({
            share_id: {"message": "Thank you!", "name": "A Friend", "occasion": "unknown"},
        }), encoding="utf-8")
        self.assertIn(b"Thank you!", self.client.get(f"/card/{share_id}").data)
        self.assertEqual(self.client.get(f"/api/share/{share_id}").get_json()["theme"]["label"], "Just Because")
        missing = self.client.get("/card/missing")
        self.assertEqual(missing.status_code, 404)
        self.assertIn(b"Card unavailable", missing.data)

    def test_failed_save_preserves_existing_shares(self):
        created = self.client.post("/api/share", json={"message": "Existing card"}).get_json()
        original = self.store.read_bytes()
        with patch.object(self.service.Path, "replace", side_effect=OSError("unwritable")):
            failed = self.client.post("/api/share", json={"message": "New card"})
        self.assertEqual(failed.status_code, 503)
        self.assertNotIn("url", failed.get_json())
        self.assertEqual(self.store.read_bytes(), original)
        self.assertIn(b"Existing card", self.client.get(created["url"]).data)

    def test_invalid_payloads_return_bad_request(self):
        for payload in ([], {"message": []}, {"message": " "}, {"message": "Hello", "occasion": {}}):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post("/api/share", json=payload).status_code, 400)
        response = self.client.post("/api/kyle-card", json={"name": None})
        self.assertEqual(response.status_code, 400)

    def test_generated_card_can_be_shared(self):
        completion = self.service.client.chat.completions.create
        completion.return_value.choices = [
            SimpleNamespace(message=SimpleNamespace(content="Congratulations on graduating!")),
        ]
        generated = self.client.post("/api/kyle-card", json={
            "name": "Sam", "occasion": "graduation", "language": "english",
        })
        self.assertEqual(generated.status_code, 200)
        self.assertEqual(generated.headers["X-Cache"], "MISS")
        self.assertEqual(completion.call_count, 1)
        card = generated.get_json()
        shared = self.client.post("/api/share", json={
            "name": "Sam", "occasion": card["occasion"], "message": card["message"],
        })
        page = self.client.get(shared.get_json()["url"])
        self.assertIn(b"Congratulations on graduating!", page.data)

    def test_analytics_requires_configured_key(self):
        with patch.dict(os.environ, {"ADMIN_KEY": ""}):
            self.assertEqual(self.client.get("/api/analytics").status_code, 401)
        with patch.dict(os.environ, {"ADMIN_KEY": "test-admin"}):
            self.assertEqual(self.client.get("/api/analytics").status_code, 401)
            response = self.client.get("/api/analytics", headers={"X-Admin-Key": "test-admin"})
            self.assertEqual(response.status_code, 200)
