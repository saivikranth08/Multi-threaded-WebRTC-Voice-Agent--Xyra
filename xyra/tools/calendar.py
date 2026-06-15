# ─────────────────────────────────────────────
#  XYRA — Google Calendar Integration Tools
#  Exposes calendar viewing and event drafting to LangGraph
# ─────────────────────────────────────────────

import os
import re
import datetime
import logging
import webbrowser
import urllib.parse
import asyncio

logger = logging.getLogger("xyra.tools.calendar")

def format_datetime_for_google(dt: datetime.datetime) -> str:
    """Formats a datetime object to YYYYMMDDTHHMMSS."""
    return dt.strftime("%Y%m%dT%H%M%S")

def parse_datetime(dt_str: str) -> datetime.datetime:
    """Robustly parses datetime strings into a datetime object."""
    dt_str = dt_str.strip()
    
    # Try common formats
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y%m%dT%H%M%S",
        "%Y%m%d"
    ):
        try:
            return datetime.datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
            
    # Try parsing via fromisoformat
    try:
        # Replace Z with UTC offset for standard isoformat parsing
        s = dt_str.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(s)
    except Exception:
        pass

    # If all parsing fails, return current time as fallback
    logger.warning(f"Could not parse datetime string: {dt_str}. Falling back to now.")
    return datetime.datetime.now()

async def draft_calendar_event_tool(
    title: str,
    start_time: str,
    end_time: str = None,
    details: str = "",
    location: str = ""
) -> str:
    """
    Open Google Calendar in the default browser with a pre-filled event creation page.
    Use this when Vickyy asks to add, schedule, or create a calendar event or meeting.

    Parameters:
    - title: The title/subject of the event.
    - start_time: ISO-formatted start date/time (e.g. '2026-06-12T14:30:00').
    - end_time: ISO-formatted end date/time. If not provided, defaults to 1 hour after start_time.
    - details: Description of the event.
    - location: Location of the event.
    """
    try:
        start_dt = parse_datetime(start_time)
        
        if end_time:
            end_dt = parse_datetime(end_time)
        else:
            end_dt = start_dt + datetime.timedelta(hours=1)
            
        start_str = format_datetime_for_google(start_dt)
        end_str = format_datetime_for_google(end_dt)
        
        params = {
            "action": "TEMPLATE",
            "text": title,
            "dates": f"{start_str}/{end_str}",
            "details": details,
            "location": location
        }
        
        query = urllib.parse.urlencode(params)
        url = f"https://calendar.google.com/calendar/render?{query}"
        
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: webbrowser.open(url))
        
        return f"DRAFTED_SUCCESS: Google Calendar draft opened for '{title}'."
    except Exception as e:
        logger.error(f"Error opening calendar draft: {e}")
        return f"❌ Error drafting calendar event: {e}"

async def view_calendar_tool(date: str = None, view: str = "day") -> str:
    """
    Open Google Calendar to a specific date and view mode.
    Use this when Vickyy asks to show, open, check, or view his calendar.

    Parameters:
    - date: ISO-formatted date (e.g. '2026-06-12'). Defaults to today.
    - view: The calendar view. Options: 'day', 'week', 'month'. Defaults to 'day'.
    """
    try:
        if date:
            dt = parse_datetime(date)
        else:
            dt = datetime.datetime.now()
            
        view = view.lower().strip()
        if view not in ("day", "week", "month"):
            view = "day"
            
        url = f"https://calendar.google.com/calendar/r/{view}/{dt.year}/{dt.month}/{dt.day}"
        
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: webbrowser.open(url))
        
        return f"SUCCESS: Opened calendar for {dt.strftime('%Y-%m-%d')} in {view} view."
    except Exception as e:
        logger.error(f"Error opening calendar view: {e}")
        return f"❌ Error opening calendar view: {e}"
