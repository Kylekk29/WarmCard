# Warmcard - AI Greeting Card Generator

A Flask-based web application that generates personalized greeting cards using AI (DeepSeek API). Supports multiple occasions, tones, languages, and lengths.

## Features

- **12 Occasions**: Birthday, Christmas, New Year, Valentine's, Anniversary, Graduation, Get Well, Thank You, Congratulations, Apology, Friendship, Encouragement
- **5 Tones**: Heartfelt, Funny, Formal, Poetic, Casual
- **3 Languages**: Chinese, English, Mixed
- **3 Lengths**: Short, Medium, Long
- AI-powered message generation via DeepSeek API
- Response caching for performance
- Rate limiting per IP
- Shareable card links
- Analytics tracking

## Prerequisites

- Python 3.12+
- A DeepSeek API key (or any OpenAI-compatible API)

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Kylekk29/warmcard.git
   cd warmcard
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file:
   ```env
   AI_API_KEY=your_deepseek_api_key
   AI_MODEL=deepseek-chat
   AI_BASE_URL=https://api.deepseek.com
   ADMIN_KEY=your_admin_key
   ```

5. Run the application:
   ```bash
   python app.py
   ```

The server starts at `http://localhost:5000`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/occasions` | List all occasions, tones, languages, lengths |
| POST | `/api/kyle-card` | Generate a greeting card |
| POST | `/api/share` | Create a shareable card |
| GET | `/api/share/<id>` | Retrieve a shared card |
| GET | `/api/health` | Health check with stats |
| GET | `/api/analytics` | Analytics (requires admin key) |

### Generate a Card

```json
POST /api/kyle-card
{
  "name": "Alice",
  "occasion": "birthday",
  "tone": "heartfelt",
  "language": "chinese",
  "length": "medium",
  "sender": "Bob"
}
```

## Deployment

The app is designed to run on Linux servers. Logs are stored at `/home/xmascard/logs/`.
