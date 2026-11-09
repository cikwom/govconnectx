from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReportCreate(BaseModel):
    title: str
    description: str
    category: str
    latitude: float
    longitude: float
    address: str | None = None
    incident_state_code: str | None = Field(default=None, max_length=12)
    incident_lga_code: str | None = Field(default=None, max_length=16)

    @field_validator("incident_state_code", "incident_lga_code")
    @classmethod
    def normalize_location_code(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else None


class ReportResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    latitude: float
    longitude: float
    address: str | None
    incident_state_code: str | None = None
    incident_lga_code: str | None = None
    status: str
    sla_due_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
