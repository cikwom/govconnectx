from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class FeedbackResponse(BaseModel):
    id: int
    report_id: int
    rating: int
    comment: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EscalationCreate(BaseModel):
    urgency: str = Field(default="high", pattern="^(normal|high|critical)$")
    reason: str = Field(min_length=10, max_length=2000)


class EscalationReview(BaseModel):
    status: str = Field(pattern="^(ACKNOWLEDGED|ACTION_REQUIRED|CLOSED)$")


class ListingCreate(BaseModel):
    listing_type: str = Field(pattern="^(lost|found)$")
    title: str = Field(min_length=4, max_length=180)
    description: str = Field(min_length=10, max_length=3000)
    location_text: str = Field(min_length=3, max_length=300)
    state_code: str | None = Field(default=None, max_length=12)
    lga_code: str | None = Field(default=None, max_length=16)
    contact_instructions: str = Field(min_length=5, max_length=500)


class ListingResponse(BaseModel):
    id: int
    listing_type: str
    title: str
    description: str
    location_text: str
    state_code: str | None
    lga_code: str | None
    contact_instructions: str
    created_at: datetime
    expires_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class ListingModeration(BaseModel):
    moderation_status: str = Field(pattern="^(APPROVED|REJECTED)$")


class ServiceDirectoryCreate(BaseModel):
    name: str = Field(min_length=3, max_length=180)
    category: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=10, max_length=2000)
    address: str = Field(min_length=3, max_length=400)
    state_code: str | None = Field(default=None, max_length=12)
    lga_code: str | None = Field(default=None, max_length=16)
    phone: str | None = Field(default=None, max_length=40)
    website: HttpUrl | None = None


class ServiceDirectoryResponse(BaseModel):
    id: int
    name: str
    category: str
    description: str
    address: str
    state_code: str | None
    lga_code: str | None
    phone: str | None
    website: str | None
    is_verified: bool
    model_config = ConfigDict(from_attributes=True)
