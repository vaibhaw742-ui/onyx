from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session

from onyx.db.models import Watch, User
from onyx.utils.logger import setup_logger

logger = setup_logger()


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


def mark_watch_item_as_checked(
    db_session: Session,
    watch_id: int,
    user_id: UUID,
) -> Watch | None:
    """Mark a watch item as checked by updating last_checked timestamp."""
    return update_watch_item(
        db_session=db_session,
        watch_id=watch_id,
        user_id=user_id,
        last_checked=datetime.utcnow(),
    )


def get_all_active_watch_items(
    db_session: Session,
) -> list[Watch]:
    """Get all active watch items across all users (for background jobs)."""
    stmt = select(Watch).where(Watch.is_active == True).order_by(Watch.added_date.desc())
    result = db_session.execute(stmt)
    return list(result.scalars().all())
