from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportAttachmentResponse(BaseModel):
    id: int
    report_id: int
    uploaded_by_user_id: int
    original_filename: str
    content_type: str
    size_bytes: int
    sha256: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
