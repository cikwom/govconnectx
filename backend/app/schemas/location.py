from pydantic import BaseModel, Field


class WardCreate(BaseModel):
    code: str = Field(min_length=2, max_length=24)
    name: str = Field(min_length=2, max_length=150)
    lga_code: str = Field(min_length=1, max_length=16)


class CommunityCreate(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=180)
    ward_code: str = Field(min_length=2, max_length=24)
