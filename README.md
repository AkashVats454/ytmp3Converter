# ytmp3Converter

A FastAPI backend that accepts a YouTube URL, converts the audio to MP3, returns a download link, and supports cleanup of generated files.

## Features

- POST `/api/v1/convert` to convert a YouTube URL to MP3.
- GET `/api/v1/download/{file_name}` to fetch the MP3 file.
- DELETE `/api/v1/download/{file_name}` to remove the file from the local `downloads/` folder.
- Background cleanup loop removes files that are older than 6 hours.

## Project Structure

- `app/main.py` – FastAPI app entrypoint
- `app/api/v1/routes.py` – API endpoints
- `app/schemas/conversion.py` – Pydantic request/response models
- `app/services/youtube_service.py` – YouTube-to-MP3 conversion service
- `app/services/file_cleanup.py` – local file deletion and auto-cleanup
- `tests/test_api.py` – unit tests

## Run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## YouTube authentication / age-restricted videos

If a video requires authentication, age verification, or bot protection, set the `YTDLP_COOKIES_FILE` environment variable to the path of a browser-exported `cookies.txt` file before starting the service. Example:

```bash
export YTDLP_COOKIES_FILE=/tmp/cookies.txt
```

On Windows PowerShell:

```powershell
$env:YTDLP_COOKIES_FILE = 'C:\path\to\cookies.txt'
```

If you want Render to create the file at startup, store the cookie contents in a secret environment variable named `YTDLP_COOKIES_CONTENT` and point `YTDLP_COOKIES_FILE` at the desired path. Example:

```bash
export YTDLP_COOKIES_FILE=/tmp/cookies.txt
export YTDLP_COOKIES_CONTENT="$(cat /path/to/cookies.txt)"
```

On Render, store the raw cookie file contents in a secret environment variable and set:

- `YTDLP_COOKIES_FILE=/tmp/cookies.txt`
- `YTDLP_COOKIES_CONTENT=<your cookies.txt content>`

## Frontend consumption

1. Call `POST /api/v1/convert` with:
   ```json
   {
     "url": "https://www.youtube.com/watch?v=..."
   }
   ```
2. The response provides:
   ```json
   {
     "status": "success",
     "file_name": "example.mp3",
     "download_url": "/api/v1/download/example.mp3"
   }
   ```
3. In the React UI, use the `download_url` to start the download.
4. After the browser download completes, call `DELETE /api/v1/download/{file_name}` to remove the local file.
5. If the UI never issues the delete request, the backend cleanup thread will delete files older than 6 hours automatically.

