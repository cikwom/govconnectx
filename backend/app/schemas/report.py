from datetime import datetime
import math

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ReportCreate(BaseModel):
    title: str
    description: str
    category: str
    latitude: float
    longitude: float
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    address: str | None = None
    incident_state_code: str | None = Field(default=None, max_length=12)
    incident_lga_code: str | None = Field(default=None, max_length=16)

    @field_validator("latitude", "longitude", "gps_latitude", "gps_longitude")
    @classmethod
    def validate_coordinates(cls, value: float | None, info):
        if value is None:
            return value
        if not math.isfinite(value):
            raise ValueError("Coordinates must be finite numbers")
        limit = 90 if info.field_name in ("latitude", "gps_latitude") else 180
        if not -limit <= value <= limit:
            raise ValueError(f"{info.field_name} must be between {-limit} and {limit}")
        return value

    @model_validator(mode="after")
    def gps_coordinates_must_be_paired(self):
        if (self.gps_latitude is None) != (self.gps_longitude is None):
            raise ValueError("Share both GPS latitude and longitude, or neither")
        return self

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
    department_id: int | None = None
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    location_review_status: str = "not_provided"
    location_reviewed_by_user_id: int | None = None
    location_reviewed_at: datetime | None = None
    location_review_note: str | None = None
    status: str
    sla_due_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
