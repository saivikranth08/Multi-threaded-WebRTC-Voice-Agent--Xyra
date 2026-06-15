# ─────────────────────────────────────────────
#  XYRA — System Tools
#  Tools related to system info, time, hardware
# ─────────────────────────────────────────────

from datetime import datetime
import psutil
import pytz


# ── Tool Definitions ──────────────────────────

def get_current_time(timezone: str = "Asia/Kolkata") -> str:
    """
    Get the current date and time.
    Use this when the user asks what time it is,
    what today's date is, or anything about current time.
    Default timezone is India (Asia/Kolkata).
    """
    try:
        tz = pytz.timezone(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        return f"❌ Unknown timezone '{timezone}'. Please use a valid timezone like 'Asia/Kolkata' or 'America/New_York'."
    now = datetime.now(tz)
    return now.strftime("Current time: %I:%M %p | Date: %A, %d %B %Y | Timezone: %Z")


def get_system_info(dummy: str = "") -> str:
    """
    Get current system hardware status.
    Use this when the user asks about CPU usage, RAM,
    battery level, disk space, or overall system health.
    """
    # CPU
    cpu = psutil.cpu_percent(interval=1)

    # RAM
    ram = psutil.virtual_memory()
    ram_used = round(ram.used / (1024 ** 3), 1)
    ram_total = round(ram.total / (1024 ** 3), 1)
    ram_percent = ram.percent

    # Disk — iterate all real physical partitions (covers C:, D:, etc. on Windows)
    disk_lines = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            used  = round(usage.used  / (1024 ** 3), 1)
            total = round(usage.total / (1024 ** 3), 1)
            disk_lines.append(f"  {part.mountpoint}: {used}GB / {total}GB ({usage.percent}%)")
        except PermissionError:
            continue
    disk_str = "\n".join(disk_lines) if disk_lines else "  N/A"

    # Battery
    battery = psutil.sensors_battery()
    if battery:
        bat_info = f"{round(battery.percent)}% | {'Charging' if battery.power_plugged else 'On Battery'}"
    else:
        bat_info = "No battery (desktop)"

    return (
        f"CPU Usage    : {cpu}%\n"
        f"RAM Usage    : {ram_used}GB / {ram_total}GB ({ram_percent}%)\n"
        f"Disk Usage   :\n{disk_str}\n"
        f"Battery      : {bat_info}"
    )


def open_camera(dummy: str = "") -> str:
    """
    Open the default camera application on the user's laptop/system.
    Use this when the user asks to open the camera, turn on the camera,
    take a picture, photo, or start the webcam.
    """
    import os
    import subprocess
    try:
        if os.name == 'nt':
            subprocess.run("start microsoft.windows.camera:", shell=True, check=True)
            return "Camera application opened successfully."
        else:
            return "Opening camera is only supported on Windows systems currently."
    except Exception as e:
        return f"Failed to open camera: {str(e)}"


def system_action(action_type: str, target: str) -> str:
    """
    Perform system commands or open applications and websites.
    
    Parameters:
    - action_type: Must be one of:
      * 'open_app': Open a system or desktop app. target should be the app name (e.g. 'chrome', 'spotify', 'vscode', 'calc', 'notepad', 'taskmgr').
      * 'open_website': Open a specific website URL in the browser. target should be the URL (e.g. 'https://github.com').
      * 'search_web_browser': Search the web in the user's default browser. target should be the search query (e.g. 'how to learn asyncio').
      * 'system_command': Control OS power/security state. target must be 'lock', 'sleep', or 'screen_off'.
    - target: The specific app name, URL, search query, or system command to run.
    """
    import os
    import subprocess
    import webbrowser
    import urllib.parse

    if os.name != 'nt':
        return "System control tools are only supported on Windows currently."

    action_type = action_type.lower().strip()
    target = target.strip()

    try:
        if action_type == 'open_app':
            app_map = {
                "chrome": "start chrome",
                "vscode": "code",
                "vs code": "code",
                "code": "code",
                "spotify": "start spotify",
                "discord": "start discord",
                "slack": "start slack",
                "calc": "calc",
                "calculator": "calc",
                "notepad": "notepad",
                "taskmgr": "taskmgr",
                "task manager": "taskmgr",
                "cmd": "start cmd",
                "command prompt": "start cmd",
                "powershell": "start powershell"
            }
            
            app_name = target.lower()
            cmd = app_map.get(app_name)
            if cmd:
                subprocess.run(cmd, shell=True, check=True)
                return f"Successfully opened {target}."
            else:
                # Safe fallback: use explorer to open the app without shell interpolation
                subprocess.run(["cmd", "/c", "start", "", target], shell=False, check=True)
                return f"Attempted to open {target}."

        elif action_type == 'open_website':
            url = target
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            webbrowser.open(url)
            return f"Opened website: {url}."

        elif action_type == 'search_web_browser':
            query_encoded = urllib.parse.quote(target)
            url = f"https://www.google.com/search?q={query_encoded}"
            webbrowser.open(url)
            return f"Opened browser search for: '{target}'."

        elif action_type == 'system_command':
            cmd_type = target.lower()
            if cmd_type == 'lock':
                subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True, check=True)
                return "System locked successfully."
            elif cmd_type == 'sleep':
                ps_cmd = "Add-Type -Assembly System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState('Suspend', $false, $false);"
                subprocess.run(f'powershell -Command "{ps_cmd}"', shell=True, check=True)
                return "System put to sleep successfully."
            elif cmd_type == 'screen_off':
                ps_cmd = "(Add-Type '[DllImport(\"user32.dll\")] public static extern int SendMessage(int hWnd, int hMsg, int wParam, int lParam);' -Name a -PassThru)::SendMessage(-1, 0x0112, 0xF170, 2)"
                subprocess.run(f'powershell -Command "{ps_cmd}"', shell=True, check=True)
                return "Screen turned off successfully."
            else:
                return f"Unknown system command: {target}. Supported: 'lock', 'sleep', 'screen_off'."

        else:
            return f"Unknown action type: {action_type}. Supported: 'open_app', 'open_website', 'search_web_browser', 'system_command'."

    except Exception as e:
        return f"Action failed: {str(e)}"


# ── Registration Helper ───────────────────────

def register_system_tools(mcp):
    """Register all system tools to the MCP server."""
    mcp.tool()(get_current_time)
    mcp.tool()(get_system_info)
    mcp.tool()(open_camera)
    mcp.tool()(system_action)
