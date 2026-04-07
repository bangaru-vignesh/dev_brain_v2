import time
import requests
import pygetwindow as gw
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================
BACKEND_API_URL = "http://localhost:8001/api/events/"
MIN_DURATION_SEC = 30           # Ignore noise under 30 seconds
FOCUS_DURATION_SEC = 1200       # 20 minutes = Focus session
CONTEXT_REPORT_INTERVAL = 3600  # Report switches every 1 hour (3600 sec)
POLL_INTERVAL_SEC = 2           # Check active window every 2 seconds

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_active_window_title():
    """Safely get the currently active window title."""
    try:
        window = gw.getActiveWindow()
        return window.title if window else None
    except Exception:
        # Failsafe in case of permission issues or OS locking
        return None

def clean_app_name(title):
    """Normalize window titles into clean application names."""
    if not title:
        return "Unknown"
    
    title_lower = title.lower()
    
    if "visual studio code" in title_lower or "vscode" in title_lower:
        return "VSCode"
    elif "youtube" in title_lower:
        # Even if in Chrome, YouTube is distinct
        return "YouTube"
    elif "chrome" in title_lower or "edge" in title_lower or "brave" in title_lower:
        return "Browser"
    elif "spotify" in title_lower:
        return "Spotify"
    elif "notion" in title_lower:
        return "Notion"
    elif "terminal" in title_lower or "powershell" in title_lower or "cmd" in title_lower:
        return "Terminal"
    else:
        return "Other"

def categorize_app(app_name):
    """Map clean application names to semantic behavior categories."""
    mapping = {
        "VSCode": "coding",
        "Terminal": "coding",
        "Browser": "learning",
        "YouTube": "distraction", # Or 'learning' depending on your model
        "Notion": "learning",
        "Spotify": "distraction"
    }
    return mapping.get(app_name, "other")

def send_to_backend(event_payload):
    """Send JSON event payload to the FastAPI backend."""
    try:
        res = requests.post(BACKEND_API_URL, json=event_payload, timeout=5)
        if res.status_code in [200, 201]:
            print(f"✅ Sent: {event_payload.get('event_type')} | {event_payload.get('app', '')}")
        else:
            print(f"⚠️ API Error ({res.status_code}): {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error sending event: {e}")

# ==========================================
# MAIN AGENT LOOP
# ==========================================
def run_agent():
    print("🚀 Desktop Signal Agent starting...")
    print(f"Watching for focus > {FOCUS_DURATION_SEC}s and noise < {MIN_DURATION_SEC}s.")
    
    current_raw_title = get_active_window_title()
    current_clean_app = clean_app_name(current_raw_title)
    start_time = time.time()
    
    # State tracking
    switch_count = 0
    last_switch_report_time = time.time()

    try:
        while True:
            time.sleep(POLL_INTERVAL_SEC)
            
            now = time.time()
            new_raw_title = get_active_window_title()
            new_clean_app = clean_app_name(new_raw_title)

            # --- BEHAVIOR 1 & 4: APP CHANGE & CONTEXT SWITCHING ---
            if new_raw_title != current_raw_title:
                duration = now - start_time
                
                # --- BEHAVIOR 3: MINIMUM DURATION FILTER ---
                if current_clean_app != "Unknown" and duration >= MIN_DURATION_SEC:
                    
                    # Core Usage Event
                    usage_event = {
                        "event_type": "app_usage",
                        "app": current_clean_app,
                        "category": categorize_app(current_clean_app),
                        "duration_seconds": int(duration),
                        "timestamp": datetime.now().isoformat()
                    }
                    send_to_backend(usage_event)
                    
                    # --- BEHAVIOR 5: FOCUS DETECTION ---
                    if duration >= FOCUS_DURATION_SEC:
                        focus_event = {
                            "event_type": "focus_session",
                            "app": current_clean_app,
                            "category": categorize_app(current_clean_app),
                            "duration_seconds": int(duration),
                            "timestamp": datetime.now().isoformat()
                        }
                        print(f"🎯 FOCUS SESSION DETECTED: {int(duration/60)} minutes in {current_clean_app}")
                        send_to_backend(focus_event)

                # If the underlying 'clean' app actually changed, count a context switch
                if new_clean_app != current_clean_app:
                    switch_count += 1
                
                # Reset counters for the new window
                current_raw_title = new_raw_title
                current_clean_app = new_clean_app
                start_time = now

            # --- HOURLY CONTEXT SWITCH REPORTING ---
            if now - last_switch_report_time >= CONTEXT_REPORT_INTERVAL:
                switch_event = {
                    "event_type": "context_switch",
                    "count": switch_count,
                    "interval_seconds": CONTEXT_REPORT_INTERVAL,
                    "timestamp": datetime.now().isoformat()
                }
                print(f"🔄 Hourly Switch Report: {switch_count} switches")
                send_to_backend(switch_event)
                
                # Reset hourly tracking
                switch_count = 0
                last_switch_report_time = now

    except KeyboardInterrupt:
        print("\n🛑 Agent stopped by user.")

if __name__ == "__main__":
    run_agent()
