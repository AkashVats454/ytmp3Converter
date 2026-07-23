from pydantic import BaseModel, Field


class ConvertRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL to convert to MP3")
    retention_minutes: int | None = Field(default=None, ge=1, le=5, description="Minutes before the generated file auto-deletes")


class ConvertResponse(BaseModel):
    status: str = Field(default="success")
    file_name: str
    download_url: str
    message: str = Field(default="MP3 ready for download")
    retention_minutes: int = Field(default=6)
    auto_delete_after_minutes: int = Field(default=6)


class DeleteResponse(BaseModel):
    status: str = Field(default="deleted")
    message: str
