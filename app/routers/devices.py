import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Device


# /devices から始まるAPIをまとめるルーター
router = APIRouter(
    prefix="/devices",
    tags=["devices"]
)


# =========================
# リクエスト・レスポンス定義
# =========================

class DeviceCreate(BaseModel):
    """
    機器を新規登録するときに受け取るデータ
    """
    hostname: str
    ip_address: str
    subnet: Optional[str] = None
    role: Optional[str] = None
    memo: Optional[str] = None


class DeviceUpdate(BaseModel):
    """
    機器情報を更新するときに受け取るデータ

    Optional にしているので、
    更新したい項目だけ送ればよい
    """
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    subnet: Optional[str] = None
    role: Optional[str] = None
    memo: Optional[str] = None


class DeviceResponse(BaseModel):
    """
    APIレスポンスとして返すデータ
    """
    id: int
    hostname: str
    ip_address: str
    subnet: Optional[str] = None
    role: Optional[str] = None
    memo: Optional[str] = None

    class Config:
        # SQLAlchemyモデルをPydanticレスポンスに変換できるようにする
        from_attributes = True


# =========================
# 共通処理
# =========================

def get_device_or_404(device_id: int, db: Session) -> Device:
    """
    指定されたIDの機器を取得する共通関数
    見つからない場合は404エラーを返す
    """
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=404,
            detail="Device not found."
        )

    return device


# =========================
# API本体
# =========================

@router.get("/", response_model=list[DeviceResponse])
def list_devices(
    hostname: Optional[str] = None,
    ip_address: Optional[str] = None,
    subnet: Optional[str] = None,
    role: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    IP台帳に登録されている機器一覧を取得するAPI
    検索条件を指定すると、条件に合う機器だけを返す。
    検索例:
    - /devices/
    - /devices/?hostname=switch
    - /devices/?ip_address=10.100
    - /devices/?subnet=10.100.0.0/24
    - /devices/?role=switch
    - /devices/?keyword=test
    """

    query = db.query(Device)

    # ホスト名で部分一致検索
    if hostname:
        query = query.filter(Device.hostname.ilike(f"%{hostname}%"))

    # IPアドレスで部分一致検索
    if ip_address:
        query = query.filter(Device.ip_address.ilike(f"%{ip_address}%"))

    # サブネットで部分一致検索
    if subnet:
        query = query.filter(Device.subnet.ilike(f"%{subnet}%"))

    # ロールで部分一致検索
    if role:
        query = query.filter(Device.role.ilike(f"%{role}%"))

    # キーワード検索
    # hostname / ip_address / subnet / role / memo のどれかに一致すれば返す
    if keyword:
        from sqlalchemy import or_

        query = query.filter(
            or_(
                Device.hostname.ilike(f"%{keyword}%"),
                Device.ip_address.ilike(f"%{keyword}%"),
                Device.subnet.ilike(f"%{keyword}%"),
                Device.role.ilike(f"%{keyword}%"),
                Device.memo.ilike(f"%{keyword}%"),
            )
        )

    devices = query.order_by(Device.id.asc()).all()

    return devices


@router.post("/", response_model=DeviceResponse)
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    """
    IP台帳に機器を1件登録するAPI
    """

    # 同じIPアドレスがすでに登録されていないか確認
    existing_device = db.query(Device).filter(
        Device.ip_address == device.ip_address
    ).first()

    if existing_device:
        raise HTTPException(
            status_code=400,
            detail="This IP address is already registered."
        )

    # DBに保存するDeviceオブジェクトを作成
    new_device = Device(
        hostname=device.hostname,
        ip_address=device.ip_address,
        subnet=device.subnet,
        role=device.role,
        memo=device.memo
    )

    # DBへ追加
    db.add(new_device)

    # 変更を確定
    db.commit()

    # DB側で採番された id などを再読み込み
    db.refresh(new_device)

    return new_device


@router.get("/export-csv")
def export_devices_csv(db: Session = Depends(get_db)):
    """
    IP台帳に登録されている機器一覧をCSVで出力するAPI

    Excelで直接開いても文字化けしにくいように、
    日本語Windows向けの CP932 / Shift_JIS で出力する。
    """

    devices = db.query(Device).order_by(Device.id.asc()).all()

    # まず文字列としてCSVを作成
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "id",
        "hostname",
        "ip_address",
        "subnet",
        "role",
        "memo",
        "created_at",
        "updated_at"
    ])

    for device in devices:
        writer.writerow([
            device.id,
            device.hostname,
            device.ip_address,
            device.subnet or "",
            device.role or "",
            device.memo or "",
            device.created_at.isoformat() if device.created_at else "",
            device.updated_at.isoformat() if device.updated_at else "",
        ])

    # CSV文字列をCP932でバイト列に変換
    csv_bytes = output.getvalue().encode("cp932", errors="replace")

    # バイト列として返す
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv; charset=shift_jis",
        headers={
            "Content-Disposition": "attachment; filename=devices.csv"
        }
    )



@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: int, db: Session = Depends(get_db)):
    """
    指定したIDの機器情報を1件取得するAPI
    """

    device = get_device_or_404(device_id, db)

    return device


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: int,
    update_data: DeviceUpdate,
    db: Session = Depends(get_db)
):
    """
    指定したIDの機器情報を更新するAPI
    """

    # 更新対象の機器を取得
    device = get_device_or_404(device_id, db)

    # IPアドレスを変更する場合、同じIPが他の機器で使われていないか確認
    if update_data.ip_address is not None and update_data.ip_address != device.ip_address:
        existing_device = db.query(Device).filter(
            Device.ip_address == update_data.ip_address
        ).first()

        if existing_device:
            raise HTTPException(
                status_code=400,
                detail="This IP address is already registered."
            )

    # 送られてきた項目だけ更新する
    if update_data.hostname is not None:
        device.hostname = update_data.hostname

    if update_data.ip_address is not None:
        device.ip_address = update_data.ip_address

    if update_data.subnet is not None:
        device.subnet = update_data.subnet

    if update_data.role is not None:
        device.role = update_data.role

    if update_data.memo is not None:
        device.memo = update_data.memo

    # 変更を確定
    db.commit()

    # 更新後の内容を再読み込み
    db.refresh(device)

    return device


@router.delete("/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    """
    指定したIDの機器情報を削除するAPI
    """

    # 削除対象の機器を取得
    device = get_device_or_404(device_id, db)

    # DBから削除
    db.delete(device)

    # 変更を確定
    db.commit()

    return {
        "message": "Device deleted successfully.",
        "deleted_id": device_id
    }



@router.post("/import-csv")
async def import_devices_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    CSVファイルからIP台帳データを一括登録・更新するAPI

    CSV列:
    - hostname
    - ip_address
    - subnet
    - role
    - memo

    動作:
    - ip_address が未登録なら新規追加
    - ip_address が既存なら hostname / subnet / role / memo を更新
    """

    # CSVファイルか簡易チェック
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="CSVファイルをアップロードしてください。"
        )

    # アップロードされたファイルを読み込み
    content = await file.read()

    # UTF-8 BOM付きCSVにも対応
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="CSVの文字コードはUTF-8で保存してください。"
        )

    # CSVを辞書形式で読み込む
    csv_file = io.StringIO(text)
    reader = csv.DictReader(csv_file)

    required_columns = {"hostname", "ip_address"}

    # ヘッダー確認
    if not reader.fieldnames:
        raise HTTPException(
            status_code=400,
            detail="CSVヘッダーが見つかりません。"
        )

    missing_columns = required_columns - set(reader.fieldnames)

    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"必須列が不足しています: {', '.join(missing_columns)}"
        )

    created_count = 0
    updated_count = 0
    skipped_count = 0
    errors = []

    for row_number, row in enumerate(reader, start=2):
        hostname = (row.get("hostname") or "").strip()
        ip_address = (row.get("ip_address") or "").strip()
        subnet = (row.get("subnet") or "").strip() or None
        role = (row.get("role") or "").strip() or None
        memo = (row.get("memo") or "").strip() or None

        # 必須項目チェック
        if not hostname or not ip_address:
            skipped_count += 1
            errors.append({
                "row": row_number,
                "reason": "hostname または ip_address が空です。"
            })
            continue

        # 同じIPアドレスの機器があるか確認
        existing_device = db.query(Device).filter(
            Device.ip_address == ip_address
        ).first()

        if existing_device:
            # 既存IPなら更新
            existing_device.hostname = hostname
            existing_device.subnet = subnet
            existing_device.role = role
            existing_device.memo = memo
            updated_count += 1
        else:
            # 未登録IPなら新規追加
            new_device = Device(
                hostname=hostname,
                ip_address=ip_address,
                subnet=subnet,
                role=role,
                memo=memo
            )
            db.add(new_device)
            created_count += 1

    # DBへ反映
    db.commit()

    return {
        "message": "CSV import completed.",
        "created_count": created_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count,
        "errors": errors
    }




