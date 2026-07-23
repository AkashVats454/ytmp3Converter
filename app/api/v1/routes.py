from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from yt_dlp.utils import DownloadError

from app.schemas.conversion import ConvertRequest, ConvertResponse, DeleteResponse
from app.services import file_cleanup
from app.services.youtube_service import YouTubeConverter

router = APIRouter(prefix="/api/v1")


@router.post("/convert", response_model=ConvertResponse)
def convert_to_mp3(payload: ConvertRequest) -> ConvertResponse:
    retention_minutes = payload.retention_minutes or 6

    try:
        converter = YouTubeConverter(output_dir=file_cleanup.DOWNLOADS_DIR)
        file_path = converter.download_audio(payload.url)
    except DownloadError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to convert this YouTube URL. The video may be unavailable, age-restricted, or blocked for audio extraction. Details: {exc}",
        ) from exc

    file_name = Path(file_path).name
    file_path_obj = Path(file_path)
    file_cleanup.write_retention_metadata(file_path_obj, retention_minutes)

    return ConvertResponse(
        status="success",
        file_name=file_name,
        download_url=f"/api/v1/download/{file_name}",
        message=f"MP3 ready for download. This file will auto-delete in {retention_minutes} minute(s) if you do not confirm the download.",
        retention_minutes=retention_minutes,
        auto_delete_after_minutes=retention_minutes,
    )


def _normalize_download_name(file_name: str) -> str:
    cleaned = file_name.strip().lstrip("/")
    normalized_name = Path(cleaned).name
    if normalized_name == "" or "/" in cleaned:
        normalized_name = cleaned.rsplit("/", 1)[-1]
    return normalized_name


def _resolve_file_path(file_name: str) -> Path:
    requested_name = _normalize_download_name(file_name)
    base_dir = Path(file_cleanup.DOWNLOADS_DIR)
    file_path = base_dir / requested_name

    if file_path.exists():
        return file_path

    requested_stem = Path(requested_name).stem
    requested_sanitized = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in requested_stem).lower()

    for candidate in base_dir.glob("*.mp3"):
        candidate_stem = candidate.stem
        candidate_sanitized = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in candidate_stem).lower()
        if candidate_stem == requested_stem or candidate_sanitized == requested_sanitized:
            return candidate

    return file_path


@router.get("/download/{file_name:path}")
def download_file(file_name: str) -> FileResponse:
    normalized_name = _normalize_download_name(file_name)
    file_path = _resolve_file_path(normalized_name)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    file_cleanup.cleanup_expired_files(base_dir=file_cleanup.DOWNLOADS_DIR)
    return FileResponse(path=file_path, filename=file_path.name, media_type="audio/mpeg")


@router.delete("/download/{file_name:path}", response_model=DeleteResponse)
def delete_file(file_name: str) -> DeleteResponse:
    normalized_name = _normalize_download_name(file_name)
    file_path = _resolve_file_path(normalized_name)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    file_path.unlink(missing_ok=True)
    file_cleanup._metadata_path_for(file_path).unlink(missing_ok=True)
    return DeleteResponse(status="deleted", message=f"{file_path.name} removed successfully")
