import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.location import Community, LocalGovernmentArea, State, Ward
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
    return [{"code": row.code, "name": row.name, "lga_code": row.lga_code} for row in rows]


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
    return [{"code": row.code, "name": row.name, "ward_code": row.ward_code} for row in rows]


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
