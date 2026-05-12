from fastapi import APIRouter, Depends, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Device


router = APIRouter(
    prefix="/ui",
    tags=["ui"]
)

templates = Jinja2Templates(directory="app/templates")


@router.get("/devices", response_class=HTMLResponse)
def devices_page(
    request: Request,
    keyword: str | None = None,
    db: Session = Depends(get_db)
):
    """
    IP台帳の一覧画面を表示する
    """

    query = db.query(Device)

    if keyword:
        search = f"%{keyword}%"
        query = query.filter(
            (Device.hostname.ilike(search)) |
            (Device.ip_address.ilike(search)) |
            (Device.subnet.ilike(search)) |
            (Device.role.ilike(search)) |
            (Device.memo.ilike(search))
        )

    devices = query.order_by(Device.id.asc()).all()

    return templates.TemplateResponse(
        request,
        "devices.html",
        {
            "devices": devices,
            "keyword": keyword or ""
        }
    )


@router.post("/devices/create")
def create_device_from_form(
    hostname: str = Form(...),
    ip_address: str = Form(...),
    subnet: str = Form(""),
    role: str = Form(""),
    memo: str = Form(""),
    db: Session = Depends(get_db)
):
    """
    HTMLフォームから機器を登録する
    """

    existing_device = db.query(Device).filter(
        Device.ip_address == ip_address
    ).first()

    if existing_device:
        # 既存IPの場合は更新する
        existing_device.hostname = hostname
        existing_device.subnet = subnet or None
        existing_device.role = role or None
        existing_device.memo = memo or None
    else:
        # 未登録IPの場合は新規追加する
        new_device = Device(
            hostname=hostname,
            ip_address=ip_address,
            subnet=subnet or None,
            role=role or None,
            memo=memo or None
        )
        db.add(new_device)

    db.commit()

    return RedirectResponse(
        url="/ui/devices",
        status_code=303
    )


@router.post("/devices/delete/{device_id}")
def delete_device_from_form(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    HTML画面から機器を削除する
    """

    device = db.query(Device).filter(Device.id == device_id).first()

    if device:
        db.delete(device)
        db.commit()

    return RedirectResponse(
        url="/ui/devices",
        status_code=303
    )


@router.post("/devices/import-csv")
async def import_csv_from_form(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    HTML画面からCSVをインポートする

    形式:
    hostname,ip_address,subnet,role,memo
    """

    import csv
    import io

    content = await file.read()

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Windows Excelで作ったCSVを想定してCP932も試す
        text = content.decode("cp932")

    reader = csv.DictReader(io.StringIO(text))

    for row in reader:
        hostname = (row.get("hostname") or "").strip()
        ip_address = (row.get("ip_address") or "").strip()
        subnet = (row.get("subnet") or "").strip() or None
        role = (row.get("role") or "").strip() or None
        memo = (row.get("memo") or "").strip() or None

        if not hostname or not ip_address:
            continue

        existing_device = db.query(Device).filter(
            Device.ip_address == ip_address
        ).first()

        if existing_device:
            existing_device.hostname = hostname
            existing_device.subnet = subnet
            existing_device.role = role
            existing_device.memo = memo
        else:
            new_device = Device(
                hostname=hostname,
                ip_address=ip_address,
                subnet=subnet,
                role=role,
                memo=memo
            )
            db.add(new_device)

    db.commit()

    return RedirectResponse(
        url="/ui/devices",
        status_code=303
    )
