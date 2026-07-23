import os

from fastapi.testclient import TestClient
from yt_dlp.utils import DownloadError

from app.main import app
from app.schemas.conversion import ConvertRequest
from app.services.file_cleanup import cleanup_expired_files
from app.services.youtube_service import YouTubeConverter


client = TestClient(app)


def test_convert_request_schema_validation():
    payload = ConvertRequest(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert str(payload.url).startswith("https://www.youtube.com/")


def test_convert_endpoint_returns_download_metadata(tmp_path, monkeypatch):
    file_path = tmp_path / "sample.mp3"
    file_path.write_text("audio")

    def fake_download(url: str, output_dir: str) -> str:
        return str(file_path)

    monkeypatch.setattr(YouTubeConverter, "download_audio", fake_download)

    response = client.post(
        "/api/v1/convert",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["download_url"].endswith("/download/sample.mp3")
    assert payload["file_name"] == "sample.mp3"


def test_cleanup_expired_files_deletes_old_file(tmp_path):
    old_file = tmp_path / "old.mp3"
    old_file.write_text("audio")
    old_timestamp = 60 * 60 * 24
    os.utime(old_file, (old_timestamp, old_timestamp))

    response = cleanup_expired_files(base_dir=str(tmp_path), max_age_hours=6)

    assert response == 1
    assert not old_file.exists()


def test_delete_endpoint_removes_downloaded_file(tmp_path, monkeypatch):
    file_path = tmp_path / "remove_me.mp3"
    file_path.write_text("audio")

    monkeypatch.setattr("app.services.file_cleanup.DOWNLOADS_DIR", str(tmp_path))

    response = client.delete("/api/v1/download/remove_me.mp3")

    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    assert not file_path.exists()


def test_download_endpoint_normalizes_malformed_encoded_path(tmp_path, monkeypatch):
    file_path = tmp_path / "remove_me.mp3"
    file_path.write_text("audio")

    monkeypatch.setattr("app.services.file_cleanup.DOWNLOADS_DIR", str(tmp_path))

    response = client.get(
        "/api/v1/download/%2Fapi%2Fv1%2Fdownload%2Fremove_me.mp3"
    )

    assert response.status_code == 200
    assert 'filename="remove_me.mp3"' in response.headers["content-disposition"]


def test_convert_endpoint_returns_400_for_unavailable_youtube_format(monkeypatch):
    def fake_download(url: str, output_dir: str) -> str:
        raise DownloadError("Requested format is not available")

    monkeypatch.setattr(YouTubeConverter, "download_audio", fake_download)

    response = client.post(
        "/api/v1/convert",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    )

    assert response.status_code == 400
    assert "Unable to convert this YouTube URL" in response.json()["detail"]


def test_resolve_file_path_matches_existing_downloaded_title_name(tmp_path, monkeypatch):
    existing_file = tmp_path / "Emraan Hashmi - Woh Lamhe Woh Baatein (Lyric Video) Zeher ｜ Atif Aslam.mp3"
    existing_file.write_text("audio")

    monkeypatch.setattr("app.services.file_cleanup.DOWNLOADS_DIR", str(tmp_path))

    response = client.get(
        "/api/v1/download/Emraan_Hashmi_-_Woh_Lamhe_Woh_Baatein__Lyric_Video__Zeher___Atif_Aslam.mp3"
    )

    assert response.status_code == 200
    assert 'filename*=' in response.headers["content-disposition"]
