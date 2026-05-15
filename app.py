import os
import json
import logging
import time
import hashlib
import uuid
import threading
import atexit
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from collections import defaultdict
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ========================
# Logging Configuration
# ========================
log_directory = "/home/xmascard/logs"
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(log_directory, "kyle-card.log")
analytics_file = os.path.join(log_directory, "analytics.json")
share_store_file = os.path.join(log_directory, "shares.json")

root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

file_handler = TimedRotatingFileHandler(
    log_file, when="midnight", interval=1, backupCount=30, encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(module)-15s | %(funcName)-20s | %(message)s'
))

class ColorFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
        'RESET': '\033[0m'
    }
    def format(self, record):
        log_message = super().format(record)
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        return f"{color}{log_message}{self.COLORS['RESET']}"

console_handler = logging.StreamHandler()
console_handler.setFormatter(ColorFormatter(
    '%(asctime)s | %(levelname)-8s | %(message)s'
))

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(file_handler)
log.addHandler(console_handler)

# ========================
# Share Store
# ========================
share_store = {}
share_store_lock = threading.Lock()

def save_shares():
    try:
        with share_store_lock:
            with open(share_store_file, 'w', encoding='utf-8') as f:
                json.dump(share_store, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log.error(f"Failed to save shares: {e}")

def load_shares():
    global share_store
    try:
        if os.path.exists(share_store_file):
            with open(share_store_file, 'r', encoding='utf-8') as f:
                share_store = json.load(f)
    except Exception as e:
        log.warning(f"Could not load shares: {e}")

load_shares()

# ========================
# Analytics
# ========================
analytics_data = defaultdict(lambda: {
    'total_requests': 0,
    'successful_generations': 0,
    'failed_generations': 0,
    'unique_users': set(),
    'occasion_counts': defaultdict(int),
    'tone_counts': defaultdict(int),
    'average_response_time': 0,
    'daily_counts': defaultdict(int)
})

def save_analytics():
    try:
        serializable_data = {}
        for key, data in analytics_data.items():
            serializable_data[key] = {
                'total_requests': data['total_requests'],
                'successful_generations': data['successful_generations'],
                'failed_generations': data['failed_generations'],
                'unique_users_count': len(data['unique_users']),
                'occasion_counts': dict(data['occasion_counts']),
                'tone_counts': dict(data['tone_counts']),
                'average_response_time': data['average_response_time'],
                'daily_counts': dict(data['daily_counts'])
            }
        with open(analytics_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log.error(f"Failed to save analytics: {e}")

def load_analytics():
    global analytics_data
    try:
        if os.path.exists(analytics_file):
            with open(analytics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key, value in data.items():
                    analytics_data[key] = defaultdict(lambda: 0, value)
                    analytics_data[key]['unique_users'] = set()
    except Exception as e:
        log.warning(f"Could not load analytics: {e}")

load_analytics()

def auto_save():
    while True:
        time.sleep(300)
        save_analytics()
        save_shares()

threading.Thread(target=auto_save, daemon=True).start()

# ========================
# Startup Banner
# ========================
def print_startup_banner():
    banner = """
    \u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557
    \u2551                                                                        \u2563
    \u2551  \U0001f384 Kyle's Greeting Card Generator 2025 \U0001f384                    \u2563
    \u2551                                                                        \u2563
    \u2551  \U0001f31f Server Initialized                                           \u2563
    \u2551  \U0001f4ca Analytics: Enabled                                            \u2563
    \u2551  \U0001f4dd Logging: Enhanced + Full Message Output                       \u2563
    \u2551  \U0001f3a8 AI: DeepSeek Reasoner                                          \u2563
    \u2551  \U0001f3b2 Occasions: birthday, christmas, new_year, valentine, ...        \u2563
    \u2551                                                                        \u2563
    \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d
    """
    print(banner)

print_startup_banner()
log.info("\U0001f384" * 40)
log.info(f"Server initialized at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.info(f"Log directory: {log_directory}")
log.info("\U0001f384" * 40)

# ========================
# Rate Limiting
# ========================
class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, ip, limit=10, window=60):
        with self.lock:
            now = time.time()
            self.requests[ip] = [t for t in self.requests[ip] if now - t < window]
            if len(self.requests[ip]) >= limit:
                return False
            self.requests[ip].append(now)
            return True

rate_limiter = RateLimiter()

# ========================
# Caching
# ========================
class ResponseCache:
    def __init__(self, max_size=2000, ttl=3600):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl

    def get_key(self, name, occasion, tone, language, length, sender):
        raw = f"{name.strip().lower()}:{occasion}:{tone}:{language}:{length}:{sender}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, name, occasion, tone, language, length, sender):
        key = self.get_key(name, occasion, tone, language, length, sender)
        entry = self.cache.get(key)
        if entry and time.time() - entry['timestamp'] < self.ttl:
            return entry['response']
        if entry:
            del self.cache[key]
        return None

    def set(self, name, occasion, tone, language, length, sender, response):
        key = self.get_key(name, occasion, tone, language, length, sender)
        if len(self.cache) >= self.max_size:
            oldest = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest]
        self.cache[key] = {'response': response, 'timestamp': time.time()}

cache = ResponseCache()

# ========================
# Occasion Theme Data
# ========================
OCCASIONS = {
    "birthday": {
        "label": "Birthday",
        "label_zh": "生日",
        "icon": "\U0001f389",
        "primary": "#ec4899",
        "secondary": "#f472b6",
        "gradient": "linear-gradient(135deg, #fce7f3 0%, #fbcfe8 50%, #fdf2f8 100%)",
        "bg_gradient": "radial-gradient(circle at center, #831843 0%, #4c0519 100%)",
        "particle_color": "#ec4899",
        "music_note": "Happy Birthday"
    },
    "christmas": {
        "label": "Christmas",
        "label_zh": "圣诞",
        "icon": "\U0001f384",
        "primary": "#b91c1c",
        "secondary": "#d4af37",
        "gradient": "linear-gradient(135deg, #dcfce7 0%, #bbf7d0 50%, #fef2f2 100%)",
        "bg_gradient": "radial-gradient(circle at center, #1e3f31 0%, #0f172a 100%)",
        "particle_color": "#ffffff",
        "music_note": "Jingle Bells"
    },
    "new_year": {
        "label": "New Year",
        "label_zh": "新年",
        "icon": "\U0001f386",
        "primary": "#f59e0b",
        "secondary": "#fbbf24",
        "gradient": "linear-gradient(135deg, #fef3c7 0%, #fde68a 50%, #fffbeb 100%)",
        "bg_gradient": "radial-gradient(circle at center, #1e3a5f 0%, #0f172a 100%)",
        "particle_color": "#fbbf24",
        "music_note": "Auld Lang Syne"
    },
    "valentine": {
        "label": "Valentine's",
        "label_zh": "情人节",
        "icon": "\U0001f498",
        "primary": "#e11d48",
        "secondary": "#fb7185",
        "gradient": "linear-gradient(135deg, #fce7f3 0%, #fda4af 50%, #fff1f2 100%)",
        "bg_gradient": "radial-gradient(circle at center, #881337 0%, #4c0519 100%)",
        "particle_color": "#fb7185",
        "music_note": "Love Story"
    },
    "anniversary": {
        "label": "Anniversary",
        "label_zh": "纪念日",
        "icon": "\U0001f48d",
        "primary": "#8b5cf6",
        "secondary": "#a78bfa",
        "gradient": "linear-gradient(135deg, #f5f3ff 0%, #ede9fe 50%, #faf5ff 100%)",
        "bg_gradient": "radial-gradient(circle at center, #4c1d95 0%, #1e1b4b 100%)",
        "particle_color": "#a78bfa",
        "music_note": "Perfect"
    },
    "graduation": {
        "label": "Graduation",
        "label_zh": "毕业",
        "icon": "\U0001f393",
        "primary": "#2563eb",
        "secondary": "#60a5fa",
        "gradient": "linear-gradient(135deg, #dbeafe 0%, #bfdbfe 50%, #eff6ff 100%)",
        "bg_gradient": "radial-gradient(circle at center, #1e3a8a 0%, #0f172a 100%)",
        "particle_color": "#60a5fa",
        "music_note": "Pomp and Circumstance"
    },
    "get_well": {
        "label": "Get Well",
        "label_zh": "早日康复",
        "icon": "\U0001f48a",
        "primary": "#10b981",
        "secondary": "#34d399",
        "gradient": "linear-gradient(135deg, #d1fae5 0%, #a7f3d0 50%, #ecfdf5 100%)",
        "bg_gradient": "radial-gradient(circle at center, #065f46 0%, #022c22 100%)",
        "particle_color": "#34d399",
        "music_note": "Lean on Me"
    },
    "thank_you": {
        "label": "Thank You",
        "label_zh": "感谢",
        "icon": "\U0001f970",
        "primary": "#f43f5e",
        "secondary": "#fb7185",
        "gradient": "linear-gradient(135deg, #ffe4e6 0%, #fecdd3 50%, #fff1f2 100%)",
        "bg_gradient": "radial-gradient(circle at center, #9f1239 0%, #4c0519 100%)",
        "particle_color": "#fb7185",
        "music_note": "Thank You"
    },
    "congratulations": {
        "label": "Congratulations",
        "label_zh": "祝贺",
        "icon": "\U0001f3c6",
        "primary": "#f59e0b",
        "secondary": "#fbbf24",
        "gradient": "linear-gradient(135deg, #fef3c7 0%, #fde68a 50%, #fffbeb 100%)",
        "bg_gradient": "radial-gradient(circle at center, #92400e 0%, #451a03 100%)",
        "particle_color": "#fcd34d",
        "music_note": "We Are the Champions"
    },
    "apology": {
        "label": "Apology",
        "label_zh": "道歉",
        "icon": "\U0001f9e1",
        "primary": "#6b7280",
        "secondary": "#9ca3af",
        "gradient": "linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 50%, #fafafa 100%)",
        "bg_gradient": "radial-gradient(circle at center, #374151 0%, #111827 100%)",
        "particle_color": "#9ca3af",
        "music_note": "Sorry"
    },
    "friendship": {
        "label": "Friendship",
        "label_zh": "友情",
        "icon": "\U0001f91d",
        "primary": "#14b8a6",
        "secondary": "#2dd4bf",
        "gradient": "linear-gradient(135deg, #ccfbf1 0%, #99f6e4 50%, #f0fdfa 100%)",
        "bg_gradient": "radial-gradient(circle at center, #115e59 0%, #042f2e 100%)",
        "particle_color": "#2dd4bf",
        "music_note": "See You Again"
    },
    "encouragement": {
        "label": "Encouragement",
        "label_zh": "鼓励",
        "icon": "\U0001f4aa",
        "primary": "#f97316",
        "secondary": "#fb923c",
        "gradient": "linear-gradient(135deg, #ffedd5 0%, #fed7aa 50%, #fff7ed 100%)",
        "bg_gradient": "radial-gradient(circle at center, #7c2d12 0%, #431407 100%)",
        "particle_color": "#fb923c",
        "music_note": "Eye of the Tiger"
    },
    "generic": {
        "label": "Just Because",
        "label_zh": "随心",
        "icon": "\U0001f3b5",
        "primary": "#6366f1",
        "secondary": "#818cf8",
        "gradient": "linear-gradient(135deg, #eef2ff 0%, #e0e7ff 50%, #f5f3ff 100%)",
        "bg_gradient": "radial-gradient(circle at center, #3730a3 0%, #1e1b4b 100%)",
        "particle_color": "#818cf8",
        "music_note": "Wonderful World"
    }
}

TONE_LABELS = {
    "heartfelt": "Heartfelt",
    "funny": "Funny",
    "formal": "Formal",
    "poetic": "Poetic",
    "casual": "Casual"
}

LANGUAGE_CONFIG = {
    "chinese": {
        "instruction": "请使用中文撰写，可以适当加入表情符号。",
        "signature": "From: {sender} \u2661",
        "fallback_prefix": ""
    },
    "english": {
        "instruction": "Write in English. You may use emojis sparingly.",
        "signature": "From: {sender} \u2661",
        "fallback_prefix": ""
    },
    "mixed": {
        "instruction": "以中文为主，适当穿插英文表达，可以加入表情符号。",
        "signature": "From: {sender} \u2661",
        "fallback_prefix": ""
    }
}

LENGTH_CONFIG = {
    "short": {"max_chars": 150, "instruction": "控制在100-150字之间，简洁精炼。"},
    "medium": {"max_chars": 350, "instruction": "控制在250-350字之间，内容充实。"},
    "long": {"max_chars": 600, "instruction": "控制在400-600字之间，详细深入。"}
}

# ========================
# Data Loading
# ========================
def load_personalized_data():
    data_file = "data.json"
    if not os.path.exists(data_file):
        return {}
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log.error(f"Error loading {data_file}: {e}")
        return {}

def load_prompts():
    prompts_file = "prompts.json"
    if not os.path.exists(prompts_file):
        log.error("prompts.json not found!")
        return {}
    try:
        with open(prompts_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log.error(f"Error loading prompts.json: {e}")
        return {}

personalized_data = load_personalized_data()
prompts = load_prompts()

def find_user_data(name):
    if not personalized_data:
        return None
    if name in personalized_data:
        return personalized_data[name]
    name_lower = name.lower()
    for key in personalized_data:
        if name_lower in key.lower() or key.lower() in name_lower:
            return personalized_data[key]
    return personalized_data.get("\u9ed8\u8ba4")

# ========================
# Fallback Messages
# ========================
def generate_fallback(name, occasion, tone, language, sender):
    lang = LANGUAGE_CONFIG.get(language, LANGUAGE_CONFIG["chinese"])
    signature = lang["signature"].format(sender=sender)

    fallback_by_occasion = {
        "birthday": {
            "heartfelt": f"Dear {name},\n\nWishing you the happiest birthday! May your day be filled with joy, love, and wonderful surprises. Thank you for being such an amazing part of my life.\n\n{signature}",
            "funny": f"Hey {name}!\n\nHappy birthday! \U0001f389 Hope your day is filled with cake, candles, and questionable decisions! May your Wi-Fi be strong and your hangover light! Cheers to another year of being awesome.\n\n{signature}",
            "formal": f"Dear {name},\n\nPlease accept my warmest wishes on your birthday. May the year ahead bring you continued success, happiness, and fulfillment.\n\nWith warm regards,\n{signature}"
        },
        "christmas": {
            "heartfelt": f"Dear {name},\n\nIn this special Christmas season, I send you my warmest wishes. May your days be filled with peace, joy, and love. Thank you for being in my life.\n\nMerry Christmas!\n\n{signature}",
            "funny": f"Hey {name}!\n\nMerry Christmas! \U0001f385 Santa told me you've been extra good this year \u2014 especially at being awesome! Hope your socks are full of gifts (and not just socks). Don't forget to leave cookies!\n\n{signature}",
            "formal": f"Dear {name},\n\nWishing you a blessed Christmas filled with peace and joy. May the spirit of this season bring warmth to your heart.\n\nMerry Christmas,\n{signature}"
        }
    }

    occasion_defaults = fallback_by_occasion.get(occasion, fallback_by_occasion.get("christmas"))
    if occasion_defaults and tone in occasion_defaults:
        return occasion_defaults[tone]
    return fallback_by_occasion["christmas"]["heartfelt"]

# ========================
# App Setup
# ========================
app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["*"], methods=["POST", "GET", "OPTIONS"],
     allow_headers=["Content-Type", "X-Request-ID", "X-Admin-Key"])

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024
app.config['JSON_SORT_KEYS'] = False
app.config['JSON_AS_ASCII'] = False

api_key = os.getenv("AI_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "deepseek-chat")
base_url = os.getenv("AI_BASE_URL", "https://api.deepseek.com")

if not api_key:
    log.critical("AI_API_KEY not found in environment variables!")
    exit(1)

client = OpenAI(api_key=api_key, base_url=base_url)

# ========================
# Request Tracking
# ========================
@app.before_request
def before_request():
    request.start_time = time.time()
    request.request_id = str(uuid.uuid4())[:8]
    request.client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown')

@app.after_request
def after_request(response):
    elapsed = time.time() - request.start_time
    response.headers['X-Request-ID'] = request.request_id
    response.headers['X-Response-Time'] = f"{elapsed:.3f}s"
    if request.method != 'OPTIONS':
        log.info(
            f"REQ {request.request_id} | {request.method} {request.path} | "
            f"IP: {request.client_ip} | Status: {response.status_code} | Time: {elapsed:.3f}s"
        )
    return response

# ========================
# Endpoints
# ========================

@app.route('/api/occasions', methods=['GET'])
def get_occasions():
    result = {}
    for key, val in OCCASIONS.items():
        result[key] = {
            "label": val["label"],
            "label_zh": val["label_zh"],
            "icon": val["icon"],
            "primary": val["primary"],
            "secondary": val["secondary"],
            "bg_gradient": val["bg_gradient"],
            "gradient": val["gradient"]
        }
    return jsonify({
        "occasions": result,
        "tones": TONE_LABELS,
        "languages": {k: v for k, v in LANGUAGE_CONFIG.items()},
        "lengths": {k: v for k, v in LENGTH_CONFIG.items()}
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "kyle-greeting-card",
        "version": "2025.12.2",
        "analytics": {
            "total_requests": sum(d['total_requests'] for d in analytics_data.values()),
            "unique_users": sum(len(d['unique_users']) for d in analytics_data.values()),
            "cache_size": len(cache.cache)
        }
    })

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    admin_key = request.headers.get('X-Admin-Key')
    if admin_key != os.getenv('ADMIN_KEY'):
        return jsonify({"error": "Unauthorized"}), 401

    total = {
        'total_requests': sum(d['total_requests'] for d in analytics_data.values()),
        'successful_generations': sum(d['successful_generations'] for d in analytics_data.values()),
        'failed_generations': sum(d['failed_generations'] for d in analytics_data.values()),
        'unique_users': sum(len(d['unique_users']) for d in analytics_data.values()),
        'occasion_counts': defaultdict(int),
        'tone_counts': defaultdict(int),
    }
    for d in analytics_data.values():
        for oc, c in d['occasion_counts'].items():
            total['occasion_counts'][oc] += c
        for t, c in d['tone_counts'].items():
            total['tone_counts'][t] += c

    return jsonify({"summary": total, "timestamp": datetime.now().isoformat()})

@app.route('/api/kyle-card', methods=['POST', 'OPTIONS'])
def kyle_card():
    if request.method == 'OPTIONS':
        return make_response('', 204)

    request_id = request.request_id
    client_ip = request.client_ip

    if not rate_limiter.is_allowed(client_ip):
        return jsonify({"error": "\u8bf7\u6c42\u8fc7\u4e8e\u9891\u7e41\uff0c\u8bf7\u7a0d\u540e\u518d\u8bd5", "retry_after": 60}), 429

    today = datetime.now().strftime('%Y-%m-%d')
    analytics_data[today]['total_requests'] += 1
    analytics_data[today]['daily_counts'][today] += 1

    try:
        data = request.get_json(silent=True)
        if not data:
            analytics_data[today]['failed_generations'] += 1
            return jsonify({"error": "\u65e0\u6548\u8bf7\u6c42\uff1aJSON\u683c\u5f0f\u9519\u8bef"}), 400

        name = data.get('name', '').strip()
        occasion = data.get('occasion', 'christmas').strip().lower()
        tone = data.get('tone', 'heartfelt').strip().lower()
        language = data.get('language', 'chinese').strip().lower()
        length = data.get('length', 'medium').strip().lower()
        sender = data.get('sender', 'Kyle').strip()

        if not name:
            analytics_data[today]['failed_generations'] += 1
            return jsonify({"error": "\u8bf7\u63d0\u4f9b\u540d\u5b57"}), 400
        if len(name) > 100:
            analytics_data[today]['failed_generations'] += 1
            return jsonify({"error": "\u540d\u5b57\u8fc7\u957f"}), 400
        if occasion not in OCCASIONS:
            occasion = 'christmas'
        if tone not in TONE_LABELS:
            tone = 'heartfelt'
        if language not in LANGUAGE_CONFIG:
            language = 'chinese'
        if length not in LENGTH_CONFIG:
            length = 'medium'

        # Cache check
        cached = cache.get(name, occasion, tone, language, length, sender)
        if cached:
            analytics_data[today]['successful_generations'] += 1
            analytics_data[today]['occasion_counts'][occasion] += 1
            analytics_data[today]['tone_counts'][tone] += 1
            analytics_data[today]['unique_users'].add(name)

            resp = jsonify({"message": cached, "occasion": occasion, "theme": OCCASIONS[occasion]})
            resp.headers['X-Cache'] = 'HIT'
            return resp

        record = find_user_data(name)
        lang_cfg = LANGUAGE_CONFIG[language]
        len_cfg = LENGTH_CONFIG[length]
        occasion_label = OCCASIONS[occasion]["label_zh"] if language == "chinese" else OCCASIONS[occasion]["label"]
        occasion_icon = OCCASIONS[occasion]["icon"]

        vibe_prompt = prompts.get(occasion, {}).get(tone, prompts.get("generic", {}).get(tone, ""))

        system_prompt = f"""You are creating a greeting card on behalf of {sender} for {name}.

Occasion: {occasion_label} {occasion_icon}
Tone: {tone}
Language: {lang_cfg['instruction']}

Style instructions:
{vibe_prompt}

Additional requirements:
1. Use the tone instructions above.
2. If relevant info available, naturally incorporate: {record or 'N/A'}
3. NEVER mention AI, model, assistant, or that this is AI-generated.
4. Write from the first-person perspective of {sender}.
5. Keep it sincere, warm, and personal.
6. {len_cfg['instruction']}
7. End with the signature: {lang_cfg['signature'].format(sender=sender)}
8. Use appropriate emojis for the occasion.
9. Address the recipient as {name} naturally in the body."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Write a {occasion} greeting card for {name} in a {tone} tone. Language: {language}."}
        ]

        log.info(f"REQ {request_id} | Calling AI API... | Occasion: {occasion} Tone: {tone} Lang: {language} Length: {length}")

        ai_response = client.chat.completions.create(
            model=AI_MODEL,
            messages=messages,
            temperature=1.2 if tone == "funny" else 0.9 if tone == "casual" else 0.8,
            max_tokens=800,
            timeout=45
        )

        message = ai_response.choices[0].message.content.strip()
        message = message.replace('```', '').strip()

        sig = lang_cfg["signature"].format(sender=sender)
        if sig not in message:
            message += f"\n\n{sig}"

        cache.set(name, occasion, tone, language, length, sender, message)

        analytics_data[today]['successful_generations'] += 1
        analytics_data[today]['occasion_counts'][occasion] += 1
        analytics_data[today]['tone_counts'][tone] += 1
        analytics_data[today]['unique_users'].add(name)

        response_time = time.time() - request.start_time
        analytics_data[today]['average_response_time'] = (
            analytics_data[today]['average_response_time'] * 0.9 + response_time * 0.1
        )

        resp = jsonify({"message": message, "occasion": occasion, "theme": OCCASIONS[occasion]})
        resp.headers['X-Cache'] = 'MISS'
        resp.headers['X-Generation-Time'] = f"{response_time:.3f}s"
        return resp

    except Exception as e:
        log.error(f"REQ {request_id} | Generation failed: {str(e)}", exc_info=True)
        analytics_data[today]['failed_generations'] += 1

        fallback = generate_fallback(name, occasion, tone, language, sender)
        resp = jsonify({"message": fallback, "occasion": occasion, "theme": OCCASIONS.get(occasion, OCCASIONS["christmas"])})
        resp.headers['X-Fallback'] = 'true'
        return resp

@app.route('/api/share', methods=['POST'])
def create_share():
    try:
        data = request.get_json(silent=True)
        if not data or 'message' not in data:
            return jsonify({"error": "Invalid share data"}), 400

        share_id = str(uuid.uuid4())[:12]
        share_data = {
            "message": data["message"],
            "name": data.get("name", "Friend"),
            "occasion": data.get("occasion", "generic"),
            "tone": data.get("tone", "heartfelt"),
            "sender": data.get("sender", "Kyle"),
            "created_at": datetime.now().isoformat()
        }

        with share_store_lock:
            share_store[share_id] = share_data

        return jsonify({
            "share_id": share_id,
            "url": f"/card/{share_id}",
            "share_data": share_data
        })
    except Exception as e:
        log.error(f"Share creation failed: {e}")
        return jsonify({"error": "Failed to create share"}), 500

@app.route('/api/share/<share_id>', methods=['GET'])
def get_share(share_id):
    with share_store_lock:
        data = share_store.get(share_id)
    if not data:
        return jsonify({"error": "Share not found"}), 404

    occasion_theme = OCCASIONS.get(data["occasion"], OCCASIONS["generic"])
    return jsonify({
        "share_data": data,
        "theme": occasion_theme
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(413)
def request_too_large(error):
    return jsonify({"error": "\u8bf7\u6c42\u6570\u636e\u8fc7\u5927"}), 413

@app.errorhandler(500)
def internal_error(error):
    log.error(f"Internal server error: {error}")
    return jsonify({"error": "\u670d\u52a1\u5668\u5185\u90e8\u9519\u8bef", "message": "\u8bf7\u7a0d\u540e\u518d\u8bd5"}), 500

@atexit.register
def shutdown():
    log.info("Server shutting down...")
    save_analytics()
    save_shares()
    log.info("Data saved. Goodbye! \U0001f384")

if __name__ == '__main__':
    log.info("\U0001f385 Starting Flask server...")
    log.info(f"\U0001f384 Environment: {'Production' if not app.debug else 'Development'}")
    log.info(f"\U0001f3b2 Available occasions: {', '.join(OCCASIONS.keys())}")
    log.info(f"\U0001f3a8 Available tones: {', '.join(TONE_LABELS.keys())}")

    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, use_reloader=False)
