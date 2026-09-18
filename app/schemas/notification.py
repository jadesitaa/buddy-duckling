from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationType


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: NotificationType
    title: str
    body: str
    related_habit_id: int | None
    related_partnership_id: int | None
    is_read: bool
    created_at: datetime


class UnreadCount(BaseModel):
    unread: int
