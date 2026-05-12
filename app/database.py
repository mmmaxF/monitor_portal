import os

# SQLAlchemyでデータベース接続エンジンを作るための関数
from sqlalchemy import create_engine

# sessionmaker:DB操作用のセッションを作るために使う
# declarative_base:SQLAlchemyのモデルクラス、つまりテーブル定義の土台を作るために使う
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL")


# DATABASE_URL が設定されていない場合は、アプリを起動させずにエラーにする
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Please check .env and docker-compose.yml."
    )


# SQLAlchemyのDB接続エンジンを作成する
# engine は「DBとの接続設定本体」のようなもの
# この時点では、常に即DB接続するというより、
# SQLAlchemyがこの接続情報を使える状態にしている
engine = create_engine(DATABASE_URL)


# DB操作用のセッションを作るためのファクトリ
# APIの処理では、この SessionLocal から db セッションを作り、
# SELECT / INSERT / UPDATE / DELETE などを実行する
#
# autocommit=False:
#   自動コミットしない
#   データを変更した場合は、明示的に db.commit() する
# autoflush=False:
#   SQLAlchemyが自動でDBへ変更を反映するタイミングを抑える
#   初心者向けには「勝手に中途半端な反映をしない設定」と理解してOK
# bind=engine:
#   このセッションは、上で作った engine のDB接続情報を使う
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# SQLAlchemyモデルの基底クラス
# models.py でテーブルを定義するときに使う
# この Base を継承したクラスが、DBテーブルと対応する
Base = declarative_base()


# FastAPIの各API処理でDBセッションを受け取るための関数
def get_db():
    # APIリクエストごとにDBセッションを作成する
    db = SessionLocal()
    try:
        # yield によって、呼び出し元のAPI処理へ db を渡す
        # API処理中はこの db を使ってDBを操作する
        yield db

    finally:
        # API処理が終わったら、正常終了・エラー終了に関係なくDB接続を閉じる
        # これをしないと、接続が残り続けてしまう可能性がある
        db.close()