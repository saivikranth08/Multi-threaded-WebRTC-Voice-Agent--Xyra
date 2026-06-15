# 🎙️ Multi-Threaded WebRTC Voice Agent (XYRA)

A real-time, low-latency conversational AI assistant integrated with a futuristic 3D WebGL HUD Dashboard. XYRA utilizes a multi-threaded WebRTC pipeline to achieve sub-100ms voice interaction, execute asynchronous system tools, query hybrid cache stores, and push dynamic HUD widgets directly over peer-to-peer data channels.

---

## ⚡ Features & Capabilities
* **Sub-100ms Voice Latency**: Built on LiveKit WebRTC pipeline with Silero VAD (Voice Activity Detection) and Deepgram streaming STT.
* **Futuristic HUD Dashboard**: Semi-transparent glassmorphic UI overlay with a Three.js glowing particle system and interactive audio-responsive wave canvas.
* **Multimodal Data Sync**: Sends real-time telemetry updates (weather metrics, custom news feeds) directly over WebRTC peer-to-peer data channels.
* **Hybrid Cache & State Store**: Uses PostgreSQL for persistent user profiling and Redis as an in-memory cache to retrieve recurring API lookups in **2 milliseconds**.
* **System Automation Tools**: Integrated Playwright browser automation for headless web scraping and visual screenshot auditing.

---

## 🛠️ Tech Stack
* **Language**: Python 3.11
* **Voice Agent Framework**: LiveKit Agent SDK
* **Speech-to-Text (STT)**: Deepgram WebSocket Pipeline
* **Text-to-Speech (TTS)**: Edge TTS Voice Synthesizer
* **AI Brain**: LLaMA 3.1 (via Groq Inference Engine)
* **Web Frontend**: HTML5, Vanilla CSS3 (Glassmorphism), JavaScript (ES6)
* **3D Visualizer**: Three.js (r128 WebGL)
* **Databases**: PostgreSQL (State) + Redis (Cache)
* **Scraping & Automation**: Playwright

---

## ⚙️ Project Setup

### Prerequisites
Make sure you have the following running locally on their default ports:
* **PostgreSQL** (Port 5432)
* **Redis** (Port 6379)

### 1. Clone the repository & Install dependencies
We use `uv` for fast dependency management:
```bash
git clone https://github.com/saivikranth08/Multi-threaded-WebRTC-Voice-Agent--Xyra.git
cd Multi-threaded-WebRTC-Voice-Agent--Xyra
uv sync
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory and populate your keys:
```env
LIVEKIT_API_KEY=your_livekit_key
LIVEKIT_API_SECRET=your_livekit_secret
LIVEKIT_URL=your_livekit_url

GROQ_API_KEY=your_groq_key
DEEPGRAM_API_KEY=your_deepgram_key
OPENWEATHER_API_KEY=your_openweather_key
NEWS_API_KEY=your_news_key

DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_NAME=xyra_db

REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. Initialize the Database
Set up and seed the PostgreSQL schemas:
```bash
.venv\Scripts\python -m xyra.db_init
```

### 4. Run the Application
Start the voice agent dev worker:
```bash
run_agent.bat
```
Start the local HTTP dashboard server:
```bash
run_dashboard.bat
```

Open **`http://localhost:8000`** in Chrome to launch the dashboard and click **Start Voice Session**.

---

## 📁 Project Structure
```
├── xyra/
│   ├── agent.py          # Voice agent worker logic & prompt pruner
│   ├── db.py             # Database connections (Postgres & Redis)
│   ├── db_init.py        # Database schema initializer & seeds
│   └── tools/
│       ├── database.py   # User facts & contact lookup tools
│       ├── browser.py    # Playwright browser scraper & screen captures
│       └── web.py        # OpenWeather & NewsAPI telemetry endpoints
├── frontend/
│   ├── index.html        # Glassmorphic HUD template
│   ├── style.css         # CSS parameters & glassmorphic properties
│   └── app.js            # Three.js visualizer & WebRTC receiver
├── run_dashboard.py      # HTTP server & LiveKit token emitter
└── README.md
```
