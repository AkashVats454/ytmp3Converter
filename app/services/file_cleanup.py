import os
import threading
import time
from pathlib import Path

DOWNLOADS_DIR = "downloads"
MAX_AGE_HOURS = 6


def cleanup_expired_files(base_dir: str = DOWNLOADS_DIR, max_age_hours: int = MAX_AGE_HOURS) -> int:
    base_path = Path(base_dir)
    if not base_path.exists():
        return 0

    deleted_count = 0
    now = time.time()
    max_age_seconds = max_age_hours * 3600

    for file_path in base_path.iterdir():
        if file_path.is_file() and (now - file_path.stat().st_mtime) > max_age_seconds:
            file_path.unlink(missing_ok=True)
            deleted_count += 1

    return deleted_count


def start_cleanup_loop(base_dir: str = DOWNLOADS_DIR, max_age_hours: int = MAX_AGE_HOURS, interval_seconds: int = 300) -> None:
    def worker() -> None:
        while True:
            cleanup_expired_files(base_dir=base_dir, max_age_hours=max_age_hours)
            time.sleep(interval_seconds)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
