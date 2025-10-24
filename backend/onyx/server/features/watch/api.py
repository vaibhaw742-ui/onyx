from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from onyx.auth.users import current_user
from onyx.db.engine.sql_engine import get_session
from onyx.db.models import User
from onyx.db.watch import (
    # Watch operations
    create_watch_item,
    get_watch_items_for_user,
    get_watch_item_by_id,
    update_watch_item,
    delete_watch_item,
    # Watch sources operations
    create_watch_source,
    get_watch_sources,
    get_watch_sources_by_watch_id,
    mark_watch_source_as_read,
    delete_watch_source,
    # Added sources operations
    create_added_source,
    get_added_sources_for_user,
    get_added_source_by_id,
    update_added_source,
    mark_added_source_as_read,
    delete_added_source,
)
from onyx.server.features.watch.models import (
    # Watch models
    WatchItemCreate,
    WatchItemUpdate,
    WatchItemResponse,
    WatchItemsResponse,
    # Watch sources models
    WatchSourceCreate,
    WatchSourceResponse,
    WatchSourcesResponse,
    # Added sources models
    AddedSourceCreate,
    AddedSourceUpdate,
    AddedSourceResponse,
    AddedSourcesResponse,
)
from onyx.utils.logger import setup_logger

logger = setup_logger()

router = APIRouter(prefix="/watch", tags=["watch"])


# =====================================================
# WATCH ENDPOINTS (To Watch feature)
# =====================================================

@router.post("", response_model=WatchItemResponse)
def create_watch(
    watch_data: WatchItemCreate,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> WatchItemResponse:
    """Create a new watch item."""
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
    """Get a specific watch item."""
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


# =====================================================
# WATCH_SOURCES ENDPOINTS (Watch Sources feature)
# =====================================================

@router.post("/sources", response_model=WatchSourceResponse)
def create_source(
    source_data: WatchSourceCreate,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> WatchSourceResponse:
    """Create a new watch source (admin/system use)."""
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # Verify user owns the watch item
    watch_item = get_watch_item_by_id(
        db_session=db_session,
        watch_id=source_data.watch_id,
        user_id=user.id,
    )
    if not watch_item:
        raise HTTPException(status_code=404, detail="Watch item not found")
    
    try:
        watch_source = create_watch_source(
            db_session=db_session,
            watch_id=source_data.watch_id,
            link=source_data.link,
            title=source_data.title,
            published_date=source_data.published_date,
            summary=source_data.summary,
            content=source_data.content,
        )
        return WatchSourceResponse.model_validate(watch_source)
    except Exception as e:
        logger.exception("Failed to create watch source")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources", response_model=WatchSourcesResponse)
def get_sources(
    only_new: bool = Query(False, description="Only return unread sources"),
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> WatchSourcesResponse:
    """Get all watch sources for the current user."""
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    sources = get_watch_sources(
        db_session=db_session,
        user_id=user.id,
        only_new=only_new,
    )
    
    new_count = sum(1 for s in sources if s.is_new)
    
    return WatchSourcesResponse(
        sources=[WatchSourceResponse.model_validate(s) for s in sources],
        total=len(sources),
        new_count=new_count,
    )


@router.get("/sources/watch/{watch_id}", response_model=WatchSourcesResponse)
def get_sources_by_watch(
    watch_id: int,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> WatchSourcesResponse:
    """Get all sources for a specific watch item."""
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    sources = get_watch_sources_by_watch_id(
        db_session=db_session,
        watch_id=watch_id,
        user_id=user.id,
    )
    
    new_count = sum(1 for s in sources if s.is_new)
    
    return WatchSourcesResponse(
        sources=[WatchSourceResponse.model_validate(s) for s in sources],
        total=len(sources),
        new_count=new_count,
    )


@router.post("/sources/{source_id}/read", response_model=WatchSourceResponse)
def mark_source_read(
    source_id: UUID,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> WatchSourceResponse:
    """Mark a watch source as read."""
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    watch_source = mark_watch_source_as_read(
        db_session=db_session,
        source_id=source_id,
        user_id=user.id,
    )
    
    if watch_source is None:
        raise HTTPException(status_code=404, detail="Watch source not found")
    
    return WatchSourceResponse.model_validate(watch_source)


@router.delete("/sources/{source_id}")
def delete_source(
    source_id: UUID,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> dict[str, str]:
    """Delete a watch source."""
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    success = delete_watch_source(
        db_session=db_session,
        source_id=source_id,
        user_id=user.id,
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Watch source not found")
    
    return {"message": "Watch source deleted successfully"}


# =====================================================
# ADDED_SOURCES ENDPOINTS (Add Sources feature)
# =====================================================

@router.post("/added-sources", response_model=AddedSourceResponse)
def create_added_source_endpoint(
    source_data: AddedSourceCreate,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> AddedSourceResponse:
    """Create a new manually added source."""
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    try:
        added_source = create_added_source(
            db_session=db_session,
            user_id=user.id,
            link=source_data.link,
            title=source_data.title,
            published_date=source_data.published_date,
            summary=source_data.summary,
            content=source_data.content,
        )
        return AddedSourceResponse.model_validate(added_source)
    except Exception as e:
        logger.exception("Failed to create added source")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/added-sources", response_model=AddedSourcesResponse)
def get_added_sources(
    only_new: bool = Query(False, description="Only return unread sources"),
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> AddedSourcesResponse:
    """Get all manually added sources for the current user."""
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    sources = get_added_sources_for_user(
        db_session=db_session,
        user_id=user.id,
        only_new=only_new,
    )
    
    new_count = sum(1 for s in sources if s.is_new)
    
    return AddedSourcesResponse(
        sources=[AddedSourceResponse.model_validate(s) for s in sources],
        total=len(sources),
        new_count=new_count,
    )


@router.get("/added-sources/{source_id}", response_model=AddedSourceResponse)
def get_added_source(
    source_id: UUID,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> AddedSourceResponse:
    """Get a specific added source."""
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    added_source = get_added_source_by_id(
        db_session=db_session,
        source_id=source_id,
        user_id=user.id,
    )
    
    if added_source is None:
        raise HTTPException(status_code=404, detail="Added source not found")
    
    return AddedSourceResponse.model_validate(added_source)


@router.patch("/added-sources/{source_id}", response_model=AddedSourceResponse)
def update_added_source_endpoint(
    source_id: UUID,
    source_data: AddedSourceUpdate,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> AddedSourceResponse:
    """Update a manually added source."""
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    added_source = update_added_source(
        db_session=db_session,
        source_id=source_id,
        user_id=user.id,
        title=source_data.title,
        link=source_data.link,
        published_date=source_data.published_date,
        summary=source_data.summary,
        content=source_data.content,
        is_new=source_data.is_new,
    )
    
    if added_source is None:
        raise HTTPException(status_code=404, detail="Added source not found")
    
    return AddedSourceResponse.model_validate(added_source)


@router.post("/added-sources/{source_id}/read", response_model=AddedSourceResponse)
def mark_added_source_read(
    source_id: UUID,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> AddedSourceResponse:
    """Mark an added source as read."""
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    added_source = mark_added_source_as_read(
        db_session=db_session,
        source_id=source_id,
        user_id=user.id,
    )
    
    if added_source is None:
        raise HTTPException(status_code=404, detail="Added source not found")
    
    return AddedSourceResponse.model_validate(added_source)


@router.delete("/added-sources/{source_id}")
def delete_added_source_endpoint(
    source_id: UUID,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> dict[str, str]:
    """Delete a manually added source."""
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    success = delete_added_source(
        db_session=db_session,
        source_id=source_id,
        user_id=user.id,
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Added source not found")
    
    return {"message": "Added source deleted successfully"}
