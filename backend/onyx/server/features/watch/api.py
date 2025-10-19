from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from onyx.auth.users import current_user
from onyx.db.engine.sql_engine import get_session
from onyx.db.models import User
from onyx.db.watch import (
    create_watch_item,
    get_watch_items_for_user,
    get_watch_item_by_id,
    update_watch_item,
    delete_watch_item,
    mark_watch_item_as_checked,
)
from onyx.server.features.watch.models import (
    WatchItemCreate,
    WatchItemUpdate,
    WatchItemResponse,
    WatchItemsResponse,
)
from onyx.utils.logger import setup_logger

logger = setup_logger()

router = APIRouter(prefix="/watch", tags=["watch"])


@router.post("", response_model=WatchItemResponse)
def create_watch(
    watch_data: WatchItemCreate,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> WatchItemResponse:
    """Create a new watch item for the current user."""
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    try:
        watch_item = create_watch_item(
            db_session=db_session,
            user_id=user.id,
            url=watch_data.url,
        )
        return WatchItemResponse.model_validate(watch_item)
    except Exception as e:
        logger.exception("Failed to create watch item")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=WatchItemsResponse)
def get_watch_items(
    include_inactive: bool = False,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> WatchItemsResponse:
    """Get all watch items for the current user."""
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    watch_items = get_watch_items_for_user(
        db_session=db_session,
        user_id=user.id,
        include_inactive=include_inactive,
    )
    
    return WatchItemsResponse(
        watch_items=[WatchItemResponse.model_validate(item) for item in watch_items],
        total=len(watch_items),
    )


@router.get("/{watch_id}", response_model=WatchItemResponse)
def get_watch_item(
    watch_id: int,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> WatchItemResponse:
    """Get a specific watch item by ID."""
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    watch_item = get_watch_item_by_id(
        db_session=db_session,
        watch_id=watch_id,
        user_id=user.id,
    )
    
    if watch_item is None:
        raise HTTPException(status_code=404, detail="Watch item not found")
    
    return WatchItemResponse.model_validate(watch_item)


@router.patch("/{watch_id}", response_model=WatchItemResponse)
def update_watch(
    watch_id: int,
    watch_data: WatchItemUpdate,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> WatchItemResponse:
    """Update a watch item."""
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    watch_item = update_watch_item(
        db_session=db_session,
        watch_id=watch_id,
        user_id=user.id,
        url=watch_data.url,
        is_active=watch_data.is_active,
    )
    
    if watch_item is None:
        raise HTTPException(status_code=404, detail="Watch item not found")
    
    return WatchItemResponse.model_validate(watch_item)


@router.delete("/{watch_id}")
def delete_watch(
    watch_id: int,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> dict[str, str]:
    """Delete a watch item."""
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    success = delete_watch_item(
        db_session=db_session,
        watch_id=watch_id,
        user_id=user.id,
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Watch item not found")
    
    return {"message": "Watch item deleted successfully"}


@router.post("/{watch_id}/check", response_model=WatchItemResponse)
def mark_as_checked(
    watch_id: int,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> WatchItemResponse:
    """Mark a watch item as checked."""
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    watch_item = mark_watch_item_as_checked(
        db_session=db_session,
        watch_id=watch_id,
        user_id=user.id,
    )
    
    if watch_item is None:
        raise HTTPException(status_code=404, detail="Watch item not found")
    
    return WatchItemResponse.model_validate(watch_item)
