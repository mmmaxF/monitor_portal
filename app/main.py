from fastapi import FastAPI

from app.database import Base, engine
from app import models
from app.routers import devices, ui



# models.py に定義したテーブルをDBに作成する
# すでに存在する場合は何もしない
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Monitor Portal API",
    description="IP台帳・監視ポータル用API",
    version="0.1.0"
)


@app.get("/")
def read_root():
    return {"message": "Monitor Portal API is running"}


# devices.py のAPIを読み込む
app.include_router(devices.router)
app.include_router(ui.router)