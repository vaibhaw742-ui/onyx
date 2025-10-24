from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update, delete, desc
from sqlalchemy.orm import Session, joinedload

from onyx.db.models import Watch, WatchSource, AddedSource, User
from onyx.utils.logger import setup_logger

logger = setup_logger()


# =====================================================
# WATCH OPERATIONS
# =====================================================

def create_watch_item(
    db_session: Session,
    user_id: UUID,
    url: str,
) -> Watch:
    """Create a new watch item for a user."""
    watch_item = Watch(
        user_id=user_id,
        url=url,
        is_active=True,
    )
    db_session.add(watch_item)
    db_session.commit()
    db_session.refresh(watch_item)
    return watch_item


def get_watch_items_for_user(
    db_session: Session,
    user_id: UUID,
    include_inactive: bool = False,
) -> list[Watch]:
    """Get all watch items for a specific user."""
    stmt = select(Watch).where(Watch.user_id == user_id)
    
    if not include_inactive:
        stmt = stmt.where(Watch.is_active == True)
    
    stmt = stmt.order_by(Watch.added_date.desc())
    
    result = db_session.execute(stmt)
    return list(result.scalars().all())


def get_watch_item_by_id(
    db_session: Session,
    watch_id: int,
    user_id: UUID,
) -> Watch | None:
    """Get a specific watch item by ID for a user."""
    stmt = select(Watch).where(
        Watch.id == watch_id,
        Watch.user_id == user_id
    )
    result = db_session.execute(stmt)
    return result.scalar_one_or_none()


def update_watch_item(
    db_session: Session,
    watch_id: int,
    user_id: UUID,
    url: str | None = None,
    is_active: bool | None = None,
    last_checked: datetime | None = None,
) -> Watch | None:
    """Update a watch item."""
    watch_item = get_watch_item_by_id(db_session, watch_id, user_id)
    
    if watch_item is None:
        return None
    
    if url is not None:
        watch_item.url = url
    if is_active is not None:
        watch_item.is_active = is_active
    if last_checked is not None:
        watch_item.last_checked = last_checked
    
    db_session.commit()
    db_session.refresh(watch_item)
    return watch_item


def delete_watch_item(
    db_session: Session,
    watch_id: int,
    user_id: UUID,
) -> bool:
    """Delete a watch item."""
    watch_item = get_watch_item_by_id(db_session, watch_id, user_id)
    
    if watch_item is None:
        return False
    
    db_session.delete(watch_item)
    db_session.commit()
    return True


# =====================================================
# WATCH_SOURCES OPERATIONS
# =====================================================

def create_watch_source(
    db_session: Session,
    watch_id: int,
    link: str,
    title: str | None = None,
    published_date: datetime | None = None,
    summary: str | None = None,
    content: str | None = None,
) -> WatchSource:
    """Create a new watch source."""
    watch_source = WatchSource(
        watch_id=watch_id,
        title=title,
        link=link,
        published_date=published_date,
        summary=summary,
        content=content,
        is_new=True,
    )
    db_session.add(watch_source)
    db_session.commit()
    db_session.refresh(watch_source)
    return watch_source


def get_watch_sources(
    db_session: Session,
    user_id: UUID,
    only_new: bool = False,
) -> list[WatchSource]:
    """Get all watch sources for a user (through their watch items)."""
    stmt = (
        select(WatchSource)
        .join(Watch, WatchSource.watch_id == Watch.id)
        .where(Watch.user_id == user_id)
    )
    
    if only_new:
        stmt = stmt.where(WatchSource.is_new == True)
    
    stmt = stmt.order_by(WatchSource.detected_at.desc())
    
    result = db_session.execute(stmt)
    return list(result.scalars().all())


def get_watch_sources_by_watch_id(
    db_session: Session,
    watch_id: int,
    user_id: UUID,
) -> list[WatchSource]:
    """Get all sources for a specific watch item."""
    # Verify user owns this watch item
    watch = get_watch_item_by_id(db_session, watch_id, user_id)
    if not watch:
        return []
    
    stmt = (
        select(WatchSource)
        .where(WatchSource.watch_id == watch_id)
        .order_by(WatchSource.detected_at.desc())
    )
    
    result = db_session.execute(stmt)
    return list(result.scalars().all())


def mark_watch_source_as_read(
    db_session: Session,
    source_id: UUID,
    user_id: UUID,
) -> WatchSource | None:
    """Mark a watch source as read (is_new = False)."""
    stmt = (
        select(WatchSource)
        .join(Watch, WatchSource.watch_id == Watch.id)
        .where(
            WatchSource.id == source_id,
            Watch.user_id == user_id
        )
    )
    
    result = db_session.execute(stmt)
    watch_source = result.scalar_one_or_none()
    
    if watch_source:
        watch_source.is_new = False
        db_session.commit()
        db_session.refresh(watch_source)
    
    return watch_source


def delete_watch_source(
    db_session: Session,
    source_id: UUID,
    user_id: UUID,
) -> bool:
    """Delete a watch source."""
    stmt = (
        select(WatchSource)
        .join(Watch, WatchSource.watch_id == Watch.id)
        .where(
            WatchSource.id == source_id,
            Watch.user_id == user_id
        )
    )
    
    result = db_session.execute(stmt)
    watch_source = result.scalar_one_or_none()
    
    if watch_source:
        db_session.delete(watch_source)
        db_session.commit()
        return True
    
    return False


# =====================================================
# ADDED_SOURCES OPERATIONS
# =====================================================

def create_added_source(
    db_session: Session,
    user_id: UUID,
    link: str,
    title: str | None = None,
    published_date: datetime | None = None,
    summary: str | None = None,
    content: str | None = None,
) -> AddedSource:
    """Create a new manually added source."""
    added_source = AddedSource(
        user_id=user_id,
        title=title,
        link=link,
        published_date=published_date,
        summary=summary,
        content=content,
        is_new=True,
    )
    db_session.add(added_source)
    db_session.commit()
    db_session.refresh(added_source)
    return added_source


def get_added_sources_for_user(
    db_session: Session,
    user_id: UUID,
    only_new: bool = False,
) -> list[AddedSource]:
    """Get all manually added sources for a user."""
    stmt = select(AddedSource).where(AddedSource.user_id == user_id)
    
    if only_new:
        stmt = stmt.where(AddedSource.is_new == True)
    
    stmt = stmt.order_by(AddedSource.created_at.desc())
    
    result = db_session.execute(stmt)
    return list(result.scalars().all())


def get_added_source_by_id(
    db_session: Session,
    source_id: UUID,
    user_id: UUID,
) -> AddedSource | None:
    """Get a specific added source."""
    stmt = select(AddedSource).where(
        AddedSource.id == source_id,
        AddedSource.user_id == user_id
    )
    result = db_session.execute(stmt)
    return result.scalar_one_or_none()


def update_added_source(
    db_session: Session,
    source_id: UUID,
    user_id: UUID,
    title: str | None = None,
    link: str | None = None,
    published_date: datetime | None = None,
    summary: str | None = None,
    content: str | None = None,
    is_new: bool | None = None,
) -> AddedSource | None:
    """Update an added source."""
    added_source = get_added_source_by_id(db_session, source_id, user_id)
    
    if added_source is None:
        return None
    
    if title is not None:
        added_source.title = title
    if link is not None:
        added_source.link = link
    if published_date is not None:
        added_source.published_date = published_date
    if summary is not None:
        added_source.summary = summary
    if content is not None:
        added_source.content = content
    if is_new is not None:
        added_source.is_new = is_new
    
    db_session.commit()
    db_session.refresh(added_source)
    return added_source


def mark_added_source_as_read(
    db_session: Session,
    source_id: UUID,
    user_id: UUID,
) -> AddedSource | None:
    """Mark an added source as read."""
    return update_added_source(
        db_session=db_session,
        source_id=source_id,
        user_id=user_id,
        is_new=False,
    )


def delete_added_source(
    db_session: Session,
    source_id: UUID,
    user_id: UUID,
) -> bool:
    """Delete an added source."""
    added_source = get_added_source_by_id(db_session, source_id, user_id)
    
    if added_source is None:
        return False
    
    db_session.delete(added_source)
    db_session.commit()
    return True
