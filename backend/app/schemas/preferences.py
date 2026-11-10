from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class UserPreferenceUpdate(BaseModel):
    email_notifications: bool = True
    in_app_notifications: bool = True
    preferred_language: str = Field(default="en", pattern="^(en|ha|yo|ig)$")


class UserPreferenceResponse(BaseModel):
    email_notifications: bool
    in_app_notifications: bool
    preferred_language: str
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
