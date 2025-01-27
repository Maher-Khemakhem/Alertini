from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import models

async def get_articles(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(models.Article).offset(skip).limit(limit))
    return result.scalars().all()

async def create_article(db: AsyncSession, article: models.Article):
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return article

async def get_comments_article(db: AsyncSession, id:int):
    """
    Fetch all comments related to a specific article.
    """
    result = await db.execute(
        select(models.Comment).where(models.Comment.article_id == id)
    )
    return result.scalars().all()
