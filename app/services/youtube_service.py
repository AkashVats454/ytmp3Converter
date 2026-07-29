import os
import shutil
import tempfile
from pathlib import Path

import yt_dlp


class YouTubeConverter:
    def __init__(self, output_dir: str = "downloads") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._cookiefile = self._prepare_cookiefile()

    def _prepare_cookiefile(self) -> str | None:
        cookie_file = os.environ.get("YTDLP_COOKIES_FILE", "/etc/secrets/cookies.txt")
        if not cookie_file:
            return None

        cookie_path = Path(cookie_file)
        if not cookie_path.exists():
            return None

        if os.access(cookie_file, os.W_OK):
            return cookie_file

        temp_cookie = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        temp_cookie.close()
        shutil.copy2(cookie_file, temp_cookie.name)
        return temp_cookie.name

    def _build_ydl_options(self, client_name: str | None = None) -> dict:
        options = {
            "outtmpl": str(self.output_dir / "%(id)s.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "0",
                }
            ],
            "merge_output_format": "mp3",
            "quiet": True,
            "noplaylist": True,
            "extract_flat": False,
            "no_warnings": False,
            "js_runtimes": {"deno": {}},
        }

        if client_name and client_name != "default":
            options["extractor_args"] = {"youtube": {"player_client": [client_name]}}

        if self._cookiefile:
            options["cookiefile"] = self._cookiefile

        return options

    def download_audio(self, url: str, output_dir: str | None = None) -> str:
        destination = Path(output_dir or self.output_dir)
        destination.mkdir(parents=True, exist_ok=True)

        client_attempts = [
            ("default", {"format": "bestaudio[ext=m4a]/bestaudio/best"}),
            ("default", {"format": "bestaudio/best"}),
            ("default", {"format": "bestvideo+bestaudio/best"}),
        ]

        if not self._cookiefile:
            client_attempts.extend([
                ("android", {"format": "bestaudio[ext=m4a]/bestaudio/best", "extractor_args": {"youtube": {"player_client": ["android"]}}}),
                ("tv_embedded", {"format": "bestaudio[ext=m4a]/bestaudio/best", "extractor_args": {"youtube": {"player_client": ["tv_embedded"]}}}),
            ])

        last_error = None

        for client_name, override_args in client_attempts:
            ydl_opts = self._build_ydl_options(client_name)
            ydl_opts.update(override_args)
            ydl_opts["outtmpl"] = str(destination / "%(id)s.%(ext)s")

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    video_id = info.get("id", "audio")
                    filename = f"{video_id}.mp3"
                    return str(destination / filename)
            except yt_dlp.utils.DownloadError as exc:
                last_error = exc
                continue

        if last_error is not None:
            raise last_error

        raise yt_dlp.utils.DownloadError("Unable to extract audio from the provided YouTube URL")
