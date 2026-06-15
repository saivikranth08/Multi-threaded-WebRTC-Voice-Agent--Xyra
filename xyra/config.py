# ─────────────────────────────────────────────
#  XYRA — Central Config
#  All API keys are loaded here ONCE.
#  Every other file imports from here.
#  Never call os.getenv() directly elsewhere.
# ─────────────────────────────────────────────

import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM ──────────────────────────────────────
GROQ_API_KEY     = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY   = os.getenv("GOOGLE_API_KEY")

# ── STT ──────────────────────────────────────
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# ── TTS ──────────────────────────────────────
# Note: Using custom EdgeTTS plugin (Free)

# ── Voice Infrastructure ──────────────────────
LIVEKIT_URL        = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY    = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# ── Email ────────────────────────────────────
GMAIL_ADDRESS      = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# ── Tools ─────────────────────────────────────
TAVILY_API_KEY      = os.getenv("TAVILY_API_KEY")
NEWS_API_KEY        = os.getenv("NEWS_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")

# ── Database & Cache ─────────────────────────
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = int(os.getenv("DB_PORT", "5432"))
DB_USER     = os.getenv("DB_USER", "xyra_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "xyra_secure_password")
DB_NAME     = os.getenv("DB_NAME", "xyra_db")

REDIS_HOST  = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT  = int(os.getenv("REDIS_PORT", "6379"))

