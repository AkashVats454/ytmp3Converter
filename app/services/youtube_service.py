from pathlib import Path

import yt_dlp


class YouTubeConverter:
    def __init__(self, output_dir: str = "downloads") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _build_ydl_options(self, client_name: str | None = None) -> dict:
        options = {
            "format": "bestaudio/best",
            "outtmpl": str(self.output_dir / "%(id)s.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "0",
                }
            ],
            "quiet": True,
            "noplaylist": True,
            "extract_flat": False,
            "no_warnings": False,
        }

        if client_name and client_name != "default":
            options["extractor_args"] = {"youtube": {"player_client": [client_name]}}

        return options

    def download_audio(self, url: str, output_dir: str | None = None) -> str:
        destination = Path(output_dir or self.output_dir)
        destination.mkdir(parents=True, exist_ok=True)

        client_attempts = [
            ("default", {}),
            ("android", {"extractor_args": {"youtube": {"player_client": ["android"]}}}),
            ("tv_embedded", {"extractor_args": {"youtube": {"player_client": ["tv_embedded"]}}}),
        ]

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
