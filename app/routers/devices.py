from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Device

router = APIRouter(prefix="/api/devices", tags=["devices"])


class DeviceCreate(BaseModel):
    ip_address: str
    mac_address: Optional[str] = None
    hostname: Optional[str] = None
    location: Optional[str] = None
    device_type: Optional[str] = None
    description: Optional[str] = None
    monitor_enabled: bool = True
    syslog_enabled: bool = True


class DeviceUpdate(BaseModel):
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    hostname: Optional[str] = None
    location: Optional[str] = None
    device_type: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    confirm_status: Optional[str] = None
    source: Optional[str] = None
    zabbix_hostid: Optional[str] = None
    syslog_hostname: Optional[str] = None
    monitor_enabled: Optional[bool] = None
    syslog_enabled: Optional[bool] = None


class DeviceResponse(BaseModel):
    id: int
    ip_address: str
    mac_address: Optional[str]
    hostname: Optional[str]
    location: Optional[str]
    device_type: Optional[str]
    description: Optional[str]
    status: str
    confirm_status: str
    source: str
    monitor_enabled: bool
    syslog_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=list[DeviceResponse])
def list_devices(db: Session = Depends(get_db)):
    return db.query(Device).order_by(Device.ip_address.asc()).all()


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return device


@router.post("", response_model=DeviceResponse)
def create_device(payload: DeviceCreate, db: Session = Depends(get_db)):
    exists = db.query(Device).filter(Device.ip_address == payload.ip_address).first()

    if exists:
        raise HTTPException(status_code=400, detail="IP address already exists")

    now = datetime.utcnow()

    device = Device(
        ip_address=payload.ip_address,
        mac_address=payload.mac_address,
        hostname=payload.hostname,
        location=payload.location,
        device_type=payload.device_type,
        description=payload.description,
        status="unknown",
        confirm_status="confirmed",
        source="manual",
        monitor_enabled=payload.monitor_enabled,
        syslog_enabled=payload.syslog_enabled,
        created_at=now,
        updated_at=now,
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(device_id: int, payload: DeviceUpdate, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    data = payload.model_dump(exclude_unset=True)

    if "ip_address" in data:
        exists = (
            db.query(Device)
            .filter(Device.ip_address == data["ip_address"], Device.id != device_id)
            .first()
        )

        if exists:
            raise HTTPException(status_code=400, detail="IP address already exists")

    for key, value in data.items():
        setattr(device, key, value)

    device.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(device)

    return device


@router.delete("/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    db.delete(device)
    db.commit()

    return {"message": "deleted"}


@router.post("/{device_id}/confirm", response_model=DeviceResponse)
def confirm_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.confirm_status = "confirmed"
    device.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(device)

    return device
