import base64
import os
from pathlib import Path

from fastapi import FastAPI

from app.api.v1.routes import router as v1_router
from app.services.file_cleanup import start_cleanup_loop

app = FastAPI(title="ytmp3Converter", version="1.0.0")
app.include_router(v1_router)

COOKIE_FILE_PATH = Path(os.environ.get("YTDLP_COOKIES_FILE", "/tmp/cookies.txt"))


def _write_cookies_file_from_env() -> None:
    raw_content = os.environ.get("YTDLP_COOKIES_CONTENT")
    b64_content = os.environ.get("YTDLP_COOKIES_CONTENT_BASE64")

    if not raw_content and not b64_content:
        return

    if b64_content:
        try:
            cookies_content = base64.b64decode(b64_content, validate=True).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            cookies_content = b64_content
    else:
        cookies_content = raw_content

    COOKIE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    COOKIE_FILE_PATH.write_text(cookies_content)


@app.on_event("startup")
def startup_event() -> None:
    _write_cookies_file_from_env()
    start_cleanup_loop()
