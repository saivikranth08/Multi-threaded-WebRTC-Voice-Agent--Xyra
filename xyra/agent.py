# ─────────────────────────────────────────────
#  XYRA — Voice Agent (Native LiveKit Architecture)
#  Zero-latency, Direct-to-Groq Pipeline
# ─────────────────────────────────────────────

import asyncio
import datetime
import json
import pytz
import logging
from typing import Annotated
from dotenv import load_dotenv

from livekit.agents import AutoSubscribe, JobContext, JobProcess, WorkerOptions, cli, llm
from livekit.agents.voice import Agent
from livekit.plugins import deepgram, groq, silero
from livekit.agents.tts import StreamAdapter
from xyra.edge_tts_plugin import EdgeTTS

# Configuration & Keys
from xyra.config import DEEPGRAM_API_KEY, GROQ_API_KEY

# Database
from xyra.db import db, save_message_log

# Import all local tools
from xyra.tools.system import get_current_time, get_system_info, open_camera, system_action
from xyra.tools.web import silent_data_fetch, get_weather, get_news
from xyra.tools.database import lookup_contact, add_contact, get_user_fact, save_user_fact
from xyra.tools.browser import (
    browser_screenshot_tool,
    browser_scrape_text_tool,
    play_youtube_video_tool,
    open_chrome_visibly,
)
from xyra.tools.calendar import draft_calendar_event_tool, view_calendar_tool

load_dotenv()
logger = logging.getLogger("xyra.agent")

# ── Function Context (Native LiveKit Tools) ──
class XyraFunctionContext(llm.ToolContext):
    def __init__(self, room=None):
        super().__init__(tools=[])
        self.room = room
        
    @llm.function_tool(description="Get the current date and time.")
    async def time(self, timezone: Annotated[str, "Timezone string, e.g., 'Asia/Kolkata'"] = "Asia/Kolkata") -> str:
        return get_current_time(timezone)

    @llm.function_tool(description="Get current system hardware status (CPU, RAM, Disk).")
    async def system_info(self) -> str:
        return get_system_info()

    @llm.function_tool(description="Open the default camera application.")
    async def camera(self) -> str:
        return open_camera()

    @llm.function_tool(description="Perform system commands or open local desktop applications.")
    async def sys_action(self, action_type: Annotated[str, "'open_app' or 'system_command'"], target: str) -> str:
        return system_action(action_type, target)

    @llm.function_tool(description="Search the internet silently to fetch raw text data for facts.")
    async def fetch_data(self, query: str) -> str:
        return await silent_data_fetch(query)

    @llm.function_tool(description="Visually pop open a Chrome browser window to show the user a website or search query.")
    async def open_chrome(self, query_or_url: str) -> str:
        return open_chrome_visibly(query_or_url)

    async def _send_ui_event(self, widget: str, data: dict):
        if not self.room:
            logger.warning("No room connected, cannot send UI event.")
            return
        try:
            payload = json.dumps({"type": "render_widget", "widget": widget, "data": data})
            logger.info(f"Publishing UI event for {widget}...")
            await self.room.local_participant.publish_data(payload.encode('utf-8'), topic="ui_events")
            logger.info(f"[OK] Published UI event for {widget} successfully.")
        except Exception as e:
            logger.error(f"Failed to publish UI event for {widget}: {e}")

    @llm.function_tool(description="Get the current weather for a specific location.")
    async def weather(self, location: str) -> str:
        data = await get_weather(location)
        asyncio.create_task(self._send_ui_event("weather", {"location": location, "result": data}))
        return data

    @llm.function_tool(description="Get the latest news headlines for a topic.")
    async def news(self, topic: str) -> str:
        data = await get_news(topic)
        asyncio.create_task(self._send_ui_event("news", {"topic": topic, "result": data}))
        return data

    @llm.function_tool(
        description="Search for a contact's details (phone, email, or relationship) by their name or family relationship (e.g., 'father', 'mother', 'brother', 'Annaya', 'Lakshmi', 'Ramesh'). Use this when the user asks for a contact's details or asks who their father/mother/brother is."
    )
    async def find_contact(self, name: str) -> str:
        return await lookup_contact(name)

    @llm.function_tool(description="Save or update a contact's phone and/or email in the database.")
    async def save_contact(self, name: str, phone: str = "", email: str = "") -> str:
        return await add_contact(name, phone, email)

    @llm.function_tool(
        description="Retrieve stored facts, habits, or profile preferences about the user Vickyy (e.g., his 'first_name', 'last_name', 'college', 'course', 'timezone', 'CGPA', 'reopening_date', 'routine', 'aim', etc.). Use this for any profile metadata query."
    )
    async def get_fact(self, topic: str) -> str:
        return await get_user_fact(topic)

    @llm.function_tool(description="Save a new fact, habit, or preference about the user Vickyy.")
    async def save_fact(self, topic: str, fact: str) -> str:
        return await save_user_fact(topic, fact)

    @llm.function_tool(description="Open a webpage and take a full-page screenshot.")
    async def screenshot(self, url: str) -> str:
        return await browser_screenshot_tool(url)

    @llm.function_tool(description="Navigate to a URL and scrape clean readable text.")
    async def scrape(self, url: str) -> str:
        return await browser_scrape_text_tool(url)

    @llm.function_tool(description="Play a YouTube video.")
    async def youtube(self, query: str) -> str:
        return await play_youtube_video_tool(query)

    @llm.function_tool(description="Draft a Google Calendar event.")
    async def draft_event(self, event_summary: str, date_str: str, time_str: str, duration_minutes: int, participants: str) -> str:
        return await draft_calendar_event_tool(event_summary, date_str, time_str, duration_minutes, participants)

    @llm.function_tool(description="View upcoming Google Calendar events.")
    async def view_events(self, date_str: str) -> str:
        return await view_calendar_tool(date_str)


# ── Agent Entrypoint ──
async def entrypoint(ctx: JobContext):
    logger.info("Initializing XYRA Native Voice Agent...")

    # Database Initialization & Task Tracking
    pending_db_tasks = set()

    def track_task(coro):
        task = asyncio.create_task(coro)
        pending_db_tasks.add(task)
        task.add_done_callback(pending_db_tasks.discard)

    try:
        await db.connect()
        logger.info("Database connected successfully.")
    except Exception as e:
        logger.warning(f"Database connection failed: {e}")

    # Connect to LiveKit Room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    logger.info("Connected to LiveKit room")
    
    # Wait for participant with timeout
    try:
        participant = await asyncio.wait_for(
            ctx.wait_for_participant(),
            timeout=30.0  # 30-second timeout for participant to join
        )
        logger.info(f"Connected to participant: {participant.identity}")
    except asyncio.TimeoutError:
        logger.error("Timeout waiting for participant to join (30s)")
        raise RuntimeError("No participant joined within 30 seconds")
    except RuntimeError as e:
        logger.error(f"Room disconnected while waiting for participant: {e}")
        raise

    # Setup Native LLM (Groq)
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing!")
    
    llm_instance = groq.LLM(
        model="llama-3.1-8b-instant",
        api_key=GROQ_API_KEY,
    )

    # Date/Time Context
    try:
        tz = pytz.timezone("Asia/Kolkata")
        now_local = datetime.datetime.now(tz)
        date_str = now_local.strftime("%B %d, %Y")
        time_str = now_local.strftime("%I:%M %p")
        day_str = now_local.strftime("%A")
    except Exception:
        date_str, time_str, day_str = "Unknown", "Unknown", "Unknown"

    system_instructions = f"""
You are XYRA, a warm, natural, and helpful AI assistant and close friend to Vickyy. 
Keep your responses conversational, concise (1-2 sentences), and human-like. 
Avoid robotic templates and do not repeat his name at the end of every sentence.

IMPORTANT: When Vickyy asks a question about himself (his career aim, name, father, etc.) and you call a tool (like 'get_fact' or 'find_contact'), you MUST read the exact values returned by the tool and speak them directly. Do not make up generic statements. If the tool returns a career aim, read the aim aloud.
Vickyy's primary profile facts (first name, timezone, location, course, etc.) are in the profile database.
Family members (father, mother, brothers) can be retrieved by using 'find_contact' (looks up phone/email) or 'get_fact' (looks up general details). 
If he asks about his father, mother, or siblings, query 'find_contact' or 'get_fact' first.
Date: {date_str} | Time: {time_str} | Day: {day_str}
"""

    fnc_ctx = XyraFunctionContext(room=ctx.room)

    from livekit.agents import AgentSession
    
    agent_obj = Agent(
        instructions=system_instructions,
        tools=llm.find_function_tools(fnc_ctx),
    )
    
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(api_key=DEEPGRAM_API_KEY),
        llm=llm_instance,
        tts=StreamAdapter(tts=EdgeTTS(voice="en-IN-NeerjaNeural"))
    )

    # Chat Log Event Tracking
    @session.on("user_speech_committed")
    def on_user_speech(msg: llm.ChatMessage):
        track_task(save_message_log(ctx.room.name, "user", msg.content))
        
        # Prune chat context to prevent Groq TPM Rate Limits (429)
        # Keep the system instruction at index 0 and the 6 most recent messages
        messages = session.chat_ctx.messages
        if len(messages) > 8:
            try:
                system_msg = messages[0]
                recent_msgs = messages[-6:]
                session.chat_ctx.messages = [system_msg] + recent_msgs
                logger.info(f"Pruned chat context to {len(session.chat_ctx.messages)} messages to stay under Groq TPM limits.")
            except Exception as e:
                logger.error(f"Error pruning chat context: {e}")

    @session.on("agent_speech_committed")
    def on_agent_speech(msg: llm.ChatMessage):
        track_task(save_message_log(ctx.room.name, "agent", msg.content))

    await session.start(agent=agent_obj, room=ctx.room)
    
    # Send Greeting
    greeting = "Hey Vickyy! How's it going?"
    session.say(greeting, allow_interruptions=True)

    # Keep alive loop
    try:
        disconnection_timeout = 0
        while ctx.room.isconnected():
            disconnection_timeout = 0
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("Agent session cancelled")
    except Exception as e:
        logger.error(f"Error in keep-alive loop: {e}")
    finally:
        logger.info("Room disconnected. Awaiting pending DB tasks...")
        if pending_db_tasks:
            await asyncio.gather(*pending_db_tasks, return_exceptions=True)
        await db.disconnect()
        logger.info("Cleanup complete.")

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="xyra"
        )
    )
