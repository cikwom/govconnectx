from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=2000)

class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DepartmentMemberUpdate(BaseModel):
    department_id: int | None

class ReportAssignmentCreate(BaseModel):
    department_id: int
    assigned_to_user_id: int | None = None
    note: str | None = Field(default=None, max_length=2000)

class StatusUpdate(BaseModel):
    status: str
    message: str | None = Field(default=None, max_length=2000)

class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    is_internal: bool = False

class AssignmentResponse(BaseModel):
    id: int
    report_id: int
    department_id: int
    assigned_to_user_id: int | None
    assigned_by_user_id: int
    note: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class HistoryResponse(BaseModel):
    id: int
    report_id: int
    changed_by_user_id: int
    old_status: str | None
    new_status: str
    message: str | None
    is_public: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CommentResponse(BaseModel):
    id: int
    report_id: int
    author_user_id: int
    body: str
    is_internal: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
