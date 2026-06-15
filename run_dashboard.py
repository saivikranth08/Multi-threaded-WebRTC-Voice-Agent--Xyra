# ─────────────────────────────────────────────
#  XYRA — Frontend Dashboard Server
#  Serves static files and generates LiveKit tokens
# ─────────────────────────────────────────────

import os
import json
import urllib.parse
from http.server import SimpleHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv
from livekit import api

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

PORT = 8000
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
import asyncio

# --- Helper function to dispatch agent asynchronously ---
async def dispatch_agent(api_key, api_secret, livekit_url):
    try:
        async with api.LiveKitAPI(livekit_url, api_key, api_secret) as lkapi:
            # Dispatch agent to xyra_room
            await lkapi.room.create_room(api.CreateRoomRequest(name="xyra_room"))
            await lkapi.agent_dispatch.create_dispatch(api.CreateAgentDispatchRequest(
                agent_name="xyra",
                room="xyra_room"
            ))
    except Exception as e:
        print(f"Error dispatching agent: {e}")

class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == "/api/token":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            api_key    = os.getenv("LIVEKIT_API_KEY")
            api_secret = os.getenv("LIVEKIT_API_SECRET")
            livekit_url = os.getenv("LIVEKIT_URL")
            if not api_key or not api_secret:
                self.wfile.write(json.dumps({"error": "Missing LIVEKIT keys in .env"}).encode())
                return
            try:
                # 1. Generate token
                token = api.AccessToken(api_key, api_secret) \
                    .with_identity("vickyy_web") \
                    .with_name("Vickyy") \
                    .with_grants(api.VideoGrants(room_join=True, room="xyra_room"))
                
                # 2. Dispatch agent into the room
                asyncio.run(dispatch_agent(api_key, api_secret, livekit_url))
                
                self.wfile.write(json.dumps({"token": token.to_jwt(), "url": livekit_url}).encode())
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            super().do_GET()

    def log_message(self, format, *args):
        pass  # Suppress access logs for clean terminal output

def main():
    if not os.path.exists(FRONTEND_DIR):
        os.makedirs(FRONTEND_DIR)
    httpd = HTTPServer(("", PORT), DashboardHandler)
    print(f"\n==============================================")
    print(f"   XYRA Dashboard Running")
    print(f"   --> Open http://localhost:{PORT} in Chrome")
    print(f"==============================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()

if __name__ == "__main__":
    main()
