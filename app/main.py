from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app import models
from app.routers import devices
from app.routers import ui


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Monitor Portal API",
    description="IP台帳・監視ポータル用API",
    version="0.1.0"
)


# CSS / JS / 画像などの静的ファイルを公開する
# 例: /static/css/devices.css
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def read_root():
    return {"message": "Monitor Portal API is running"}


app.include_router(devices.router)
app.include_router(ui.router)