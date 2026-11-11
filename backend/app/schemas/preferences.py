from datetime import datetime

import re
from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserPreferenceUpdate(BaseModel):
    email_notifications: bool = True
    in_app_notifications: bool = True
    sms_notifications: bool | None = None
    preferred_language: str = Field(default="en", pattern="^(en|ha|yo|ig)$")


class UserPreferenceResponse(BaseModel):
    email_notifications: bool
    in_app_notifications: bool
    sms_notifications: bool
    sms_consent_at: datetime | None = None
    sms_consent_revoked_at: datetime | None = None
    preferred_language: str
    phone_number: str | None = None
    phone_verified_at: datetime | None = None
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PhoneVerificationRequest(BaseModel):
    phone_number: str = Field(min_length=9, max_length=16)

    @field_validator("phone_number")
    @classmethod
    def validate_e164(cls, value: str) -> str:
        normalized = value.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if not re.fullmatch(r"\+[1-9][0-9]{7,14}", normalized):
            raise ValueError("Enter a phone number in international format, e.g. +2348012345678")
        return normalized


class PhoneVerificationConfirm(BaseModel):
    code: str = Field(pattern="^[0-9]{6}$")
