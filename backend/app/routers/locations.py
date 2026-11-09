import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.location import LocalGovernmentArea, State

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
