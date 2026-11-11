import csv
import io
import json
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.location import Community, LocalGovernmentArea, State, Ward
from app.models.audit_event import record_audit_event
from app.core.dependencies import require_roles
from app.models.user import User
from app.schemas.location import CommunityCreate, WardCreate

router = APIRouter(prefix="/api/v1/locations", tags=["Geographical locations"])


def seed_location_directory(db: Session) -> None:
    """Idempotently load the published state/LGA reference directory."""
    data_path = Path(__file__).resolve().parents[1] / "data" / "nigeria_admin_divisions.json"
    with data_path.open(encoding="utf-8") as source:
        directory = json.load(source)

    for item in directory["states"]:
        existing = db.get(State, item["code"])
        if existing is None:
            db.add(State(
                code=item["code"],
                name=item["name"],
                slug=item["slug"],
                geopolitical_zone=item["zone"],
            ))
        else:
            existing.name = item["name"]
            existing.slug = item["slug"]
            existing.geopolitical_zone = item["zone"]

    for item in directory["lgas"]:
        existing = db.get(LocalGovernmentArea, item["code"])
        if existing is None:
            db.add(LocalGovernmentArea(
                code=item["code"],
                name=item["name"],
                state_code=item["state_code"],
            ))
        else:
            existing.name = item["name"]
            existing.state_code = item["state_code"]
    db.commit()




def _parse_geography_csv(content: bytes, db: Session):
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="CSV file must be 2 MB or smaller")
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded") from None
    reader = csv.DictReader(io.StringIO(decoded))
    required = {"record_type", "code", "name", "parent_code"}
    headers = [(field or "").strip().lower() for field in (reader.fieldnames or [])]
    if not headers or not required.issubset(set(headers)):
        raise HTTPException(status_code=400, detail="CSV headers must include record_type,code,name,parent_code")
    if len(headers) != len(set(headers)):
        raise HTTPException(status_code=400, detail="CSV contains duplicate column names")
    rows, errors, seen = [], [], set()
    for line_number, raw in enumerate(reader, start=2):
        if line_number > 5002:
            raise HTTPException(status_code=413, detail="CSV may contain at most 5,000 data rows")
        row = {(key or "").strip().lower(): (value or "").strip() for key, value in raw.items() if key is not None}
        if not any(row.values()):
            continue
        kind, code = row.get("record_type", "").lower(), row.get("code", "").upper()
        name, parent = " ".join(row.get("name", "").split()), row.get("parent_code", "").upper()
        if kind not in ("ward", "community"):
            errors.append({"row": line_number, "code": code, "error": "record_type must be ward or community"})
            continue
        max_code, max_name = (24, 150) if kind == "ward" else (32, 180)
        if not code or len(code) > max_code or not name or len(name) > max_name or not parent:
            errors.append({"row": line_number, "code": code, "error": "code, name and parent_code are required and must fit documented limits"})
            continue
        key = (kind, code)
        if key in seen:
            errors.append({"row": line_number, "code": code, "error": "duplicate code within this CSV"})
            continue
        seen.add(key)
        rows.append({"row": line_number, "record_type": kind, "code": code, "name": name, "parent_code": parent})
    batch_wards = {row["code"]: row for row in rows if row["record_type"] == "ward"}
    valid = []
    for row in rows:
        if row["record_type"] == "ward":
            if db.get(LocalGovernmentArea, row["parent_code"]) is None:
                errors.append({"row": row["row"], "code": row["code"], "error": "parent_code must identify an existing LGA code"})
            elif db.get(Ward, row["code"]) is not None:
                errors.append({"row": row["row"], "code": row["code"], "error": "ward code already exists; imports never overwrite existing records"})
            else:
                valid.append(row)
        else:
            parent = db.get(Ward, row["parent_code"])
            batch_parent = batch_wards.get(row["parent_code"])
            if parent is None and batch_parent is None:
                errors.append({"row": row["row"], "code": row["code"], "error": "parent_code must identify an existing ward or a ward in this CSV"})
            elif parent is not None and not parent.is_active:
                errors.append({"row": row["row"], "code": row["code"], "error": "parent ward is inactive"})
            elif db.get(Community, row["code"]) is not None:
                errors.append({"row": row["row"], "code": row["code"], "error": "community code already exists; imports never overwrite existing records"})
            else:
                if batch_parent and db.get(LocalGovernmentArea, batch_parent["parent_code"]) is None:
                    errors.append({"row": row["row"], "code": row["code"], "error": "parent ward references an unknown LGA"})
                else:
                    valid.append(row)
    return rows, valid, errors


@router.post("/admin/import/preview")
async def preview_geography_import(
    file: UploadFile = File(...),
    source_name: str = Form(..., min_length=2, max_length=180),
    source_reference: str = Form(..., min_length=3, max_length=500),
    effective_from: date | None = Form(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("system_admin")),
):
    content = await file.read(2 * 1024 * 1024 + 1)
    rows, valid, errors = _parse_geography_csv(content, db)
    return {
        "total_rows": len(rows), "valid_rows": len(valid), "errors": errors,
        "wards": sum(row["record_type"] == "ward" for row in valid),
        "communities": sum(row["record_type"] == "community" for row in valid),
        "source_name": source_name.strip(), "source_reference": source_reference.strip(),
        "effective_from": effective_from.isoformat() if effective_from else None,
        "can_import": bool(valid) and not errors,
        "notice": "Preview only. No records have been written.",
    }


@router.post("/admin/import/commit")
async def commit_geography_import(
    file: UploadFile = File(...),
    source_name: str = Form(..., min_length=2, max_length=180),
    source_reference: str = Form(..., min_length=3, max_length=500),
    effective_from: date | None = Form(default=None),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("system_admin")),
):
    content = await file.read(2 * 1024 * 1024 + 1)
    rows, valid, errors = _parse_geography_csv(content, db)
    if errors or not valid:
        raise HTTPException(status_code=422, detail={"message": "Import was not applied. Correct every CSV error and preview again.", "errors": errors})
    now = datetime.now(timezone.utc)
    for row in valid:
        if row["record_type"] == "ward":
            db.add(Ward(code=row["code"], name=row["name"], lga_code=row["parent_code"],
                        source_name=source_name.strip(), source_reference=source_reference.strip(),
                        effective_from=effective_from, imported_at=now, imported_by_user_id=actor.id))
    db.flush()
    for row in valid:
        if row["record_type"] == "community":
            db.add(Community(code=row["code"], name=row["name"], ward_code=row["parent_code"],
                             source_name=source_name.strip(), source_reference=source_reference.strip(),
                             effective_from=effective_from, imported_at=now, imported_by_user_id=actor.id))
    record_audit_event(
        db, actor_user_id=actor.id, action="geography.bulk_imported", entity_type="geography_import",
        summary=f"Imported {len(valid)} geographic reference records",
        details={"source_name": source_name.strip(), "source_reference": source_reference.strip(),
                 "effective_from": effective_from.isoformat() if effective_from else None,
                 "wards": sum(row["record_type"] == "ward" for row in valid),
                 "communities": sum(row["record_type"] == "community" for row in valid)},
    )
    db.commit()
    return {"imported": len(valid), "wards": sum(row["record_type"] == "ward" for row in valid),
            "communities": sum(row["record_type"] == "community" for row in valid),
            "source_name": source_name.strip(), "effective_from": effective_from.isoformat() if effective_from else None}


@router.get("/states")
def list_states(db: Session = Depends(get_db)):
    states = db.query(State).order_by(State.name.asc()).all()
    return [
        {"code": item.code, "name": item.name, "geopolitical_zone": item.geopolitical_zone}
        for item in states
    ]


@router.get("/states/{state_code}/lgas")
def list_state_lgas(state_code: str, db: Session = Depends(get_db)):
    state = db.get(State, state_code.upper())
    if state is None:
        raise HTTPException(status_code=404, detail="State not found")
    lgas = (
        db.query(LocalGovernmentArea)
        .filter(LocalGovernmentArea.state_code == state.code)
        .order_by(LocalGovernmentArea.name.asc())
        .all()
    )
    return [{"code": item.code, "name": item.name, "state_code": item.state_code} for item in lgas]

 

@router.get("/lgas/{lga_code}/wards")
def list_lga_wards(lga_code: str, db: Session = Depends(get_db)):
    lga = db.get(LocalGovernmentArea, lga_code.upper())
    if lga is None:
        raise HTTPException(status_code=404, detail="LGA not found")
    rows = (
        db.query(Ward)
        .filter(Ward.lga_code == lga.code, Ward.is_active.is_(True))
        .order_by(Ward.name.asc())
        .all()
    )
    return [{
        "code": row.code, "name": row.name, "lga_code": row.lga_code,
        "source_name": row.source_name, "source_reference": row.source_reference,
        "effective_from": row.effective_from.isoformat() if row.effective_from else None,
        "imported_at": row.imported_at.isoformat() if row.imported_at else None,
    } for row in rows]


@router.get("/wards/{ward_code}/communities")
def list_ward_communities(ward_code: str, db: Session = Depends(get_db)):
    ward = db.get(Ward, ward_code.upper())
    if ward is None or not ward.is_active:
        raise HTTPException(status_code=404, detail="Ward not found")
    rows = (
        db.query(Community)
        .filter(Community.ward_code == ward.code, Community.is_active.is_(True))
        .order_by(Community.name.asc())
        .all()
    )
    return [{
        "code": row.code, "name": row.name, "ward_code": row.ward_code,
        "source_name": row.source_name, "source_reference": row.source_reference,
        "effective_from": row.effective_from.isoformat() if row.effective_from else None,
        "imported_at": row.imported_at.isoformat() if row.imported_at else None,
    } for row in rows]


@router.post("/admin/wards", status_code=status.HTTP_201_CREATED)
def create_ward(payload: WardCreate, db: Session = Depends(get_db), _: User = Depends(require_roles("system_admin"))):
    code = payload.code.strip().upper()
    lga_code = payload.lga_code.strip().upper()
    if db.get(Ward, code):
        raise HTTPException(status_code=409, detail="Ward code already exists")
    if db.get(LocalGovernmentArea, lga_code) is None:
        raise HTTPException(status_code=404, detail="LGA not found")
    row = Ward(code=code, name=" ".join(payload.name.split()), lga_code=lga_code)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"code": row.code, "name": row.name, "lga_code": row.lga_code, "is_active": row.is_active}


@router.post("/admin/communities", status_code=status.HTTP_201_CREATED)
def create_community(payload: CommunityCreate, db: Session = Depends(get_db), _: User = Depends(require_roles("system_admin"))):
    code = payload.code.strip().upper()
    ward_code = payload.ward_code.strip().upper()
    if db.get(Community, code):
        raise HTTPException(status_code=409, detail="Community code already exists")
    ward = db.get(Ward, ward_code)
    if ward is None or not ward.is_active:
        raise HTTPException(status_code=404, detail="Active ward not found")
    row = Community(code=code, name=" ".join(payload.name.split()), ward_code=ward_code)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"code": row.code, "name": row.name, "ward_code": row.ward_code, "is_active": row.is_active}
