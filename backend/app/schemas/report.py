from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportCreate(BaseModel):
    title: str
    description: str
    category: str

    latitude: float
    longitude: float

    address: str | None = None


class ReportResponse(BaseModel):
    id: int

    title: str
    description: str
    category: str

    latitude: float
    longitude: float

    address: str | None

    status: str

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)