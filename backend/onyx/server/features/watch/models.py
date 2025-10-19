from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl, field_validator


class WatchItemCreate(BaseModel):
    url: str
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that the URL is properly formatted."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class WatchItemUpdate(BaseModel):
    url: str | None = None
    is_active: bool | None = None


class WatchItemResponse(BaseModel):
    id: int
    user_id: UUID
    url: str
    added_date: datetime
    last_checked: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WatchItemsResponse(BaseModel):
    watch_items: list[WatchItemResponse]
    total: int
