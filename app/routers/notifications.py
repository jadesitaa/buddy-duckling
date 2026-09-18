from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select, update

from app.deps import CurrentUser, DbSession
from app.models.notification import Notification
from app.schemas.notification import NotificationRead, UnreadCount

me_notifications = APIRouter(prefix="/me/notifications", tags=["notifications"])
notifications = APIRouter(prefix="/notifications", tags=["notifications"])


@me_notifications.get("", response_model=list[NotificationRead])
async def list_my_notifications(
    current_user: CurrentUser, db: DbSession, unread_only: bool = False, limit: int = 50
) -> list[Notification]:
    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read.is_(False))
    result = await db.scalars(
        query.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit)
    )
    return list(result)


@me_notifications.get("/unread-count", response_model=UnreadCount)
async def unread_count(current_user: CurrentUser, db: DbSession) -> UnreadCount:
    count = await db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read.is_(False))
    )
    return UnreadCount(unread=count or 0)


@me_notifications.put("/read-all", response_model=UnreadCount)
async def mark_all_read(current_user: CurrentUser, db: DbSession) -> UnreadCount:
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    await db.commit()
    return UnreadCount(unread=0)


@notifications.put("/{notification_id}/read", response_model=NotificationRead)
async def mark_read(
    notification_id: int, current_user: CurrentUser, db: DbSession
) -> Notification:
    notification = await db.scalar(
        select(Notification).where(Notification.id == notification_id)
    )
    # A user can only ever touch their own notifications.
    if notification is None or notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )

    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return notification
