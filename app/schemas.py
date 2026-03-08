from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8)


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class LoginRequest(BaseModel):
    username: str
    password: str


class FeatureCreate(BaseModel):
    latitude: float
    longitude: float
    feature_type: str = 'guardrail_terminal'
    is_broken: bool = False
    source: str = 'user'
    source_ref: str | None = None
    confidence: float | None = None


class FeatureOut(FeatureCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2_000)


class CommentOut(BaseModel):
    id: int
    feature_id: int
    user_id: int
    body: str
    created_at: datetime

    class Config:
        from_attributes = True
