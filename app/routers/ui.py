import csv
import io
from collections import defaultdict

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
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
            or_(
                Device.hostname.ilike(search),
                Device.ip_address.ilike(search),
                Device.subnet.ilike(search),
                Device.role.ilike(search),
                Device.memo.ilike(search),
            )
        )

    devices = query.order_by(Device.subnet.asc(), Device.ip_address.asc()).all()

    # サブネットごとに機器をまとめる
    grouped_devices = defaultdict(list)

    for device in devices:
        subnet_name = device.subnet or "未設定"
        grouped_devices[subnet_name].append(device)

    # Jinja2で扱いやすい形にする
    subnet_groups = [
        {
            "subnet": subnet,
            "devices": items,
            "count": len(items)
        }
        for subnet, items in grouped_devices.items()
    ]

    total_devices = len(devices)
    total_subnets = len(subnet_groups)

    return templates.TemplateResponse(
        request,
        "devices.html",
        {
            "keyword": keyword or "",
            "devices": devices,
            "subnet_groups": subnet_groups,
            "total_devices": total_devices,
            "total_subnets": total_subnets,
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
        existing_device.hostname = hostname
        existing_device.subnet = subnet or None
        existing_device.role = role or None
        existing_device.memo = memo or None
    else:
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


@router.post("/devices/update/{device_id}")
def update_device_from_form(
    device_id: int,
    hostname: str = Form(...),
    ip_address: str = Form(...),
    subnet: str = Form(""),
    role: str = Form(""),
    memo: str = Form(""),
    db: Session = Depends(get_db)
):
    """
    HTML画面から機器情報を更新する
    """

    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        return RedirectResponse(
            url="/ui/devices",
            status_code=303
        )

    # IPアドレス変更時、他の機器と重複していないか確認
    existing_device = db.query(Device).filter(
        Device.ip_address == ip_address,
        Device.id != device_id
    ).first()

    if existing_device:
        # ひとまず画面に戻す
        # 後でエラーメッセージ表示を追加可能
        return RedirectResponse(
            url="/ui/devices",
            status_code=303
        )

    device.hostname = hostname
    device.ip_address = ip_address
    device.subnet = subnet or None
    device.role = role or None
    device.memo = memo or None

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
    """

    content = await file.read()

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
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