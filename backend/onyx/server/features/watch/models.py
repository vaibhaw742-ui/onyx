from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


# =====================================================
# WATCH MODELS
# =====================================================

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


# =====================================================
# WATCH_SOURCES MODELS
# =====================================================

class WatchSourceCreate(BaseModel):
    watch_id: int
    link: str
    title: str | None = None
    published_date: datetime | None = None
    summary: str | None = None
    content: str | None = None


class WatchSourceResponse(BaseModel):
    id: UUID
    watch_id: int
    title: str | None
    link: str
    published_date: datetime | None
    summary: str | None
    content: str | None
    is_new: bool
    detected_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class WatchSourcesResponse(BaseModel):
    sources: list[WatchSourceResponse]
    total: int
    new_count: int


# =====================================================
# ADDED_SOURCES MODELS
# =====================================================

class AddedSourceCreate(BaseModel):
    link: str
    title: str | None = None
    published_date: datetime | None = None
    summary: str | None = None
    content: str | None = None
    
    @field_validator('link')
    @classmethod
    def validate_link(cls, v: str) -> str:
        """Validate that the link is properly formatted."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Link must start with http:// or https://')
        return v


class AddedSourceUpdate(BaseModel):
    title: str | None = None
    link: str | None = None
    published_date: datetime | None = None
    summary: str | None = None
    content: str | None = None
    is_new: bool | None = None


class AddedSourceResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str | None
    link: str
    published_date: datetime | None
    summary: str | None
    content: str | None
    is_new: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AddedSourcesResponse(BaseModel):
    sources: list[AddedSourceResponse]
    total: int
    new_count: int
