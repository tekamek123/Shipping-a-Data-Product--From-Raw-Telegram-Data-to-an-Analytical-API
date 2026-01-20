from pydantic import BaseModel
from typing import List, Optional

class TopProduct(BaseModel):
    term: str
    frequency: int

class ChannelActivity(BaseModel):
    date: str
    message_count: int
    avg_views: float

class MessageSearchResult(BaseModel):
    message_id: int
    channel_name: str
    message_text: str
    views: int

class VisualContentStat(BaseModel):
    channel_name: str
    total_posts: int
    image_posts: int
    image_ratio: float
