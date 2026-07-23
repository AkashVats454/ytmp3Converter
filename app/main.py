from fastapi import FastAPI

from app.api.v1.routes import router as v1_router
from app.services.file_cleanup import start_cleanup_loop

app = FastAPI(title="ytmp3Converter", version="1.0.0")
app.include_router(v1_router)


@app.on_event("startup")
def startup_event() -> None:
    start_cleanup_loop()
