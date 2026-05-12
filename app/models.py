from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)

    ip_address = Column(String(64), unique=True, nullable=False, index=True)
    mac_address = Column(String(64), nullable=True)
    hostname = Column(String(255), nullable=True)

    location = Column(String(255), nullable=True)
    device_type = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # alive / dead / unknown
    status = Column(String(50), nullable=False, default="unknown")

    # confirmed / unconfirmed
    confirm_status = Column(String(50), nullable=False, default="confirmed")

    # manual / scan / import
    source = Column(String(50), nullable=False, default="manual")

    # Zabbix / SYSLOG連携用
    zabbix_hostid = Column(String(128), nullable=True)
    syslog_hostname = Column(String(255), nullable=True)

    monitor_enabled = Column(Boolean, nullable=False, default=True)
    syslog_enabled = Column(Boolean, nullable=False, default=True)

    first_seen_at = Column(DateTime, nullable=True)
    last_seen_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
