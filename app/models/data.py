from app.models.module import *



class RelayPostRecords(BaseModel):
    __tablename__ = "relay_post_records"

    post_key = Column(String(50), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    author_key = Column(String(50), index=True)
    likes = Column(Integer)
    post_thumbnail_url = Column(String)
    post_thumbnail_hash = Column(String(50))
    local_image_path = Column(String(500))
    local_thumbnail_path = Column(String(500))
    is_banned = Column(Boolean)
    scraped_at = Column(DateTime)
    updated_at = Column(DateTime)
    is_current = Column(Boolean)

