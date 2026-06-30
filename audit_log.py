import json
import os

LOG_FILE = os.path.join("data", "audit_log.json")


def ensure_log_file():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)


def read_log():
    ensure_log_file()
    with open(LOG_FILE, "r") as f:
        return json.load(f)


def write_log_entry(entry):
    entries = read_log()
    entries.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def get_recent_entries(limit=10):
    entries = read_log()
    return entries[-limit:]


def find_classification_by_content_id(content_id):
    entries = read_log()
    for entry in entries:
        if entry.get("event_type") == "classification" and entry.get("content_id") == content_id:
            return entry
    return None


def update_classification_status(content_id, new_status):
    entries = read_log()
    for entry in entries:
        if entry.get("event_type") == "classification" and entry.get("content_id") == content_id:
            entry["status"] = new_status
    with open(LOG_FILE, "w") as f:
        json.dump(entries, f, indent=2)
