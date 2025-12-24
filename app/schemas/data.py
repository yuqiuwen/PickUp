from datetime import datetime

from pydantic import field_serializer
from app.schemas.common import EntityModel, PageModel
from app.schemas.field import AutoFormatTimeField, TimestampField
from app.utils.dater import DT


class QPostAssetSchema(PageModel):
    post_key: str


class PostAssetSchema(EntityModel):
    id: int
    post_key: str
    version: int
    author_key: str | None = None
    likes: int | None = None
    thumbnail_url: str | None = None
    thumbnail_hash: str | None = None
    local_image_path: str | None = None
    local_thumbnail_path: str | None = None
    is_banned: bool | None = None
    scraped_at: AutoFormatTimeField() | None
    updated_at: AutoFormatTimeField() | None
    is_current: bool | None = None

    # @field_serializer("scraped_at", "updated_at")
    # def serialize_datetime(self, value: datetime | None) -> str | None:
    #     if value is None:
    #         return None
    #     return DT.fmt_time(value, "%Y-%m-%d %H:%M:%S")
