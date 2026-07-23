import json
import threading
import time
from pathlib import Path

DOWNLOADS_DIR = "downloads"
MAX_AGE_HOURS = 6


def _metadata_path_for(file_path: Path) -> Path:
    return file_path.with_suffix(f"{file_path.suffix}.meta.json")


def _load_retention_metadata(file_path: Path) -> tuple[float, int] | None:
    metadata_path = _metadata_path_for(file_path)
    if not metadata_path.exists():
        return None

    try:
        payload = json.loads(metadata_path.read_text())
    except (OSError, ValueError, json.JSONDecodeError):
        return None

    created_at = payload.get("created_at")
    retention_minutes = payload.get("retention_minutes")

    if not isinstance(created_at, (int, float)) or not isinstance(retention_minutes, int):
        return None

    if retention_minutes < 1 or retention_minutes > 5:
        return None

    return float(created_at), retention_minutes


def write_retention_metadata(file_path: Path, retention_minutes: int) -> None:
    metadata_path = _metadata_path_for(file_path)
    payload = {
        "created_at": time.time(),
        "retention_minutes": retention_minutes,
    }
    metadata_path.write_text(json.dumps(payload))


def cleanup_expired_files(base_dir: str = DOWNLOADS_DIR, max_age_hours: int = MAX_AGE_HOURS) -> int:
    base_path = Path(base_dir)
    if not base_path.exists():
        return 0

    deleted_count = 0
    now = time.time()

    for file_path in base_path.iterdir():
        if not file_path.is_file() or file_path.suffix.lower() != ".mp3":
            continue

        retention_metadata = _load_retention_metadata(file_path)
        if retention_metadata is None:
            created_at = file_path.stat().st_mtime
            max_age_seconds = max_age_hours * 3600
        else:
            created_at, retention_minutes = retention_metadata
            max_age_seconds = retention_minutes * 60

        if (now - created_at) > max_age_seconds:
            file_path.unlink(missing_ok=True)
            _metadata_path_for(file_path).unlink(missing_ok=True)
            deleted_count += 1

    return deleted_count


def start_cleanup_loop(base_dir: str = DOWNLOADS_DIR, max_age_hours: int = MAX_AGE_HOURS, interval_seconds: int = 300) -> None:
    def worker() -> None:
        while True:
            cleanup_expired_files(base_dir=base_dir, max_age_hours=max_age_hours)
            time.sleep(interval_seconds)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
