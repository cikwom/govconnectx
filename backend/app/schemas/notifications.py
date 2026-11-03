from datetime import datetime
from pydantic import BaseModel, ConfigDict

class NotificationResponse(BaseModel):
    id: int
    report_id: int | None
    event_type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime
    read_at: datetime | None
    model_config = ConfigDict(from_attributes=True)
