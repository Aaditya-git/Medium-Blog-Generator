from datetime import datetime, timezone

def today_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def timestamp_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
