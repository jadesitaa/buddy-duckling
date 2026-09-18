"""The one place notifications are created.

Everything that needs to tell a user something goes through `notify()`, so
adding another channel later (email, LINE Messaging API, push) means changing
this file only.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType


async def notify(
    db: AsyncSession,
    *,
    user_id: int,
    type: NotificationType,
    title: str,
    body: str,
    related_habit_id: int | None = None,
    related_partnership_id: int | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        related_habit_id=related_habit_id,
        related_partnership_id=related_partnership_id,
    )
    db.add(notification)
    await db.flush()
    return notification
