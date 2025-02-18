from pydantic import BaseModel
from datetime import datetime
from typing import List

class CommentSchema(BaseModel):
    id: int
    comment: str
    username: str
    user_id: str
    timestamp: datetime
    article_id: int
    created_at:datetime
    is_toxic:bool
    class Config:
        orm_mode = True


class ArticleSchema(BaseModel):
    id: int
    title: str
    summary: str
    image: str
    scraped_at: datetime
    comments: List[CommentSchema] = []

    class Config:
        orm_mode = True
