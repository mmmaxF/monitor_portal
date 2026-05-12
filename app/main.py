from fastapi import FastAPI

from app.database import Base, engine
from app.routers import devices

# 初期段階なので、起動時にテーブルを自動作成する
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="IP台帳・監視ポータル",
    version="0.1.0",
)

app.include_router(devices.router)


@app.get("/")
def root():
    return {
        "message": "IP台帳・監視ポータル API",
        "docs": "/docs",
    }
