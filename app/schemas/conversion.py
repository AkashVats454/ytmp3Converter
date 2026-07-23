from pydantic import BaseModel, Field


class ConvertRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL to convert to MP3")


class ConvertResponse(BaseModel):
    status: str = Field(default="success")
    file_name: str
    download_url: str
    message: str = Field(default="MP3 ready for download")


class DeleteResponse(BaseModel):
    status: str = Field(default="deleted")
    message: str
