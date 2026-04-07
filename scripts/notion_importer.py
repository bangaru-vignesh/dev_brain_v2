import os
import json
import requests
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================
# IMPORTANT: export NOTION_TOKEN="secret_..." before running,
# or replace the default value below with your actual token.
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "YOUR_NOTION_TOKEN_HERE")
BACKEND_API_URL = "http://localhost:8001/api/events/"
SYNC_STATE_FILE = "last_notion_sync.json"

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# ==========================================
# 1. DEDUPLICATION LOGIC
# ==========================================
def get_last_sync_time():
    """Retrieve the timestamp of the last processed page to avoid duplication."""
    if os.path.exists(SYNC_STATE_FILE):
        with open(SYNC_STATE_FILE, "r") as f:
            data = json.load(f)
            return data.get("last_sync_time")
    return None

def update_last_sync_time(last_time_str):
    """Save the latest page timestamp."""
    with open(SYNC_STATE_FILE, "w") as f:
        json.dump({"last_sync_time": last_time_str}, f)

# ==========================================
# 2. FETCH NOTION DATA
# ==========================================
def fetch_notion_pages():
    """Fetch all pages via Notion Search API."""
    url = "https://api.notion.com/v1/search"
    
    # We apply a filter to only get "page" objects (ignoring databases themselves)
    # We sort by last_edited_time ascending to process oldest updates first
    payload = {
        "filter": {
            "value": "page",
            "property": "object"
        },
        "sort": {
            "direction": "ascending",
            "timestamp": "last_edited_time"
        }
    }
    
    response = requests.post(url, headers=NOTION_HEADERS, json=payload)
    if response.status_code != 200:
        print(f"❌ Error fetching from Notion: {response.status_code}")
        print(response.text)
        return []
    
    return response.json().get("results", [])

# ==========================================
# 3. DATA EXTRACTION LOGIC
# ==========================================
def extract_page_data(page):
    """Safely extract the title and last edited time from a Notion page object."""
    # 1. Extract last updated timestamp
    last_edited_time = page.get("last_edited_time")
    
    # 2. Safely extract title
    title = "Untitled"
    # Notion properties can have dynamic keys. Usually, the title property is named "Name" or "title".
    # Iterate through properties to find the one with type "title"
    properties = page.get("properties", {})
    for prop_name, prop_data in properties.items():
        if prop_data.get("type") == "title":
            title_array = prop_data.get("title", [])
            if title_array and len(title_array) > 0:
                title = title_array[0].get("plain_text", "Untitled")
            break
            
    return title, last_edited_time

# ==========================================
# 4. API INTEGRATION
# ==========================================
def send_to_backend(title, timestamp):
    """Convert into DevBrain format and send via POST request."""
    # Event format required by your prompt
    event_data = {
        "event_type": "note_updated",
        "source": "notion",
        "title": title,
        "timestamp": timestamp
    }
    
    try:
        response = requests.post(BACKEND_API_URL, json=event_data)
        if response.status_code in [200, 201]:
            print(f"✅ Successfully sent: '{title}'")
            return True
        else:
            print(f"⚠️ Failed to send '{title}': Backend returned {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error sending to backend: {e}")
        return False

# ==========================================
# 5. MAIN ORCHESTRATION
# ==========================================
def main():
    print("🚀 Starting Notion Integration Sync...")
    last_sync = get_last_sync_time()
    
    if last_sync:
        print(f"Last sync time was: {last_sync}")
        # Note: In a production script, you would pass a timestamp filter to the Notion API.
        # The /search API lacks granular time filtering, so we filter locally.
    
    pages = fetch_notion_pages()
    print(f"Fetched {len(pages)} pages from Notion.")
    
    latest_processed_time = last_sync
    
    for page in pages:
        title, edited_time = extract_page_data(page)
        
        # Deduplication Filter: Skip if page is older than our last sync marker
        if last_sync and edited_time <= last_sync:
            continue
            
        print(f"Processing: '{title}' (Updated: {edited_time})")
        
        success = send_to_backend(title, edited_time)
        
        if success:
            # Keep track of the newest timestamp we have successfully processed
            if not latest_processed_time or edited_time > latest_processed_time:
                latest_processed_time = edited_time
                
    # Update state file at the end
    if latest_processed_time and latest_processed_time != last_sync:
        update_last_sync_time(latest_processed_time)
        print("💾 Updated sync state file.")
        
    print("🏁 Sync Complete.")

if __name__ == "__main__":
    main()
