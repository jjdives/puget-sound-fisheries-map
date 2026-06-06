import os
import json
from datetime import datetime, timedelta

def load_existing_data():
    """Loads the current openings database or initializes a new schema if missing."""
    file_path = "openings.json"
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
            
    # Default schema initialization
    return {
        "last_updated": datetime.now().isoformat()[:19],
        "openings": []
    }

def save_data(data):
    """Writes the updated database back to disk, maintaining local time formatting."""
    data["last_updated"] = datetime.now().isoformat()[:19]
    with open("openings.json", "w") as f:
        json.dump(data, f, indent=2)

def clean_expired_openings_fifo(data):
    """Filters out any opening entries where the close timestamp is older than 12 months."""
    cutoff_date = datetime.now() - timedelta(days=365)
    original_count = len(data["openings"])
    
    # Keep only openings closed within the last year, or future scheduled openings
    data["openings"] = [
        op for op in data["openings"]
        if datetime.fromisoformat(op["close_timestamp"]) >= cutoff_date
    ]
    
    truncated_count = original_count - len(data["openings"])
    if truncated_count > 0:
        print(f"[FIFO] Purged {truncated_count} records older than 12 months.")
    return data

def run_scraper():
    # 1. Load historical dataset
    database = load_existing_data()
    
    # 2. Target Feed Registry (Collected URLs to iterate)
    targets = [
        {"agency": "PNPTC", "url": "https://pnptc.org/"},
        {"agency": "Swinomish", "url": "https://www.swinomish-nsn.gov/fisheries/page/crab"},
        {"agency": "Suquamish", "url": "https://suquamish.nsn.us/home/departments/fisheries/tribal-fishing-hunting/"}
        # Additional target URLs map here
    ]
    
    new_openings_discovered = []
    
    # TODO: Integrate individual HTTP extraction and LLM structured parsing routines here.
    # Discovered records will be appended to new_openings_discovered array.
    
    # 3. Append new unique entries (Preventing duplication via UID matching)
    existing_uids = {op["uid"] for op in database["openings"]}
    for item in new_openings_discovered:
        if item["uid"] not in existing_uids:
            database["openings"].append(item)
            
    # 4. Enforce 12-month data retention ceiling
    database = clean_expired_openings_fifo(database)
    
    # 5. Commit changes to file
    save_data(database)

if __name__ == "__main__":
    run_scraper()
