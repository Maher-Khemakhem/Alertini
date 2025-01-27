from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text)
    image = Column(String)
    scraped_at = Column(DateTime)

    comments = relationship("Comment", back_populates="article")


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    comment = Column(Text)
    username = Column(String(100))
    user_id = Column(String(100))
    timestamp = Column(DateTime)
    article_id = Column(Integer, ForeignKey("articles.id"))

    article = relationship("Article", back_populates="comments")
