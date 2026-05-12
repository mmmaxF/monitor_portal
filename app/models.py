from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Device(Base):
    """
    IP台帳に登録する機器情報のテーブル定義
    """

    # PostgreSQL上のテーブル名
    __tablename__ = "devices"

    # 主キー
    id = Column(Integer, primary_key=True, index=True)

    # ホスト名・機器名
    hostname = Column(String(255), nullable=False)

    # IPアドレス
    ip_address = Column(String(50), nullable=False, unique=True, index=True)

    # サブネット
    subnet = Column(String(100), nullable=True)

    # 機器種別
    # 例: router, switch, server, pc, unknown
    role = Column(String(100), nullable=True)

    # メモ
    memo = Column(Text, nullable=True)

    # 作成日時
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 更新日時
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())