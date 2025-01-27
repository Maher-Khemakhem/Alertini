from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import tensorflow as tf
import asyncio
from .database import get_db
import pandas as pd
import pickle
from tensorflow.keras.models import load_model
from sklearn.feature_extraction.text import TfidfVectorizer
from .crud import get_articles
from .crud import get_comments_article
from . import models
app = FastAPI()

# Load the pre-trained model
df = pd.read_csv('../comments_data.csv')

# Load the TF-IDF vectorizer
with open('../tfidf_vectorizer.pkl', 'rb') as f:
    loaded_vectorizer = pickle.load(f)

# Load the trained model
loaded_model = load_model('../toxic_comment_prediction_model.h5')

# In-memory queue for notifications
notification_queue = asyncio.Queue()

# Define a Pydantic schema for the comment input
class CommentInput(BaseModel):
    content: str

@app.post("/comments/")
async def add_comment(comment: CommentInput, db: AsyncSession = Depends(get_db)):
    """
    Endpoint to add a comment and check if it's toxic.
    """
    # Process the comment
    comments = comment.content
    processed_comments = loaded_vectorizer.transform([comments])

    # Convert sparse matrix to dense array for Keras
    processed_comments_dense = processed_comments.toarray()

    # Make predictions asynchronously
    predictions = await asyncio.to_thread(loaded_model.predict, processed_comments_dense)
    predictions = (predictions > 0.5).astype(int)

    # Check if the comment is toxic
    is_toxic = bool(predictions)

    # Send a notification if the comment is toxic
    if is_toxic:
        await notification_queue.put({"content": comment.content, "toxic": True})

    return {
        "comment": comment.content,
        "toxic": is_toxic,
        "message": "Comment added successfully."
    }

@app.get("/notifications/")
async def notifications():
    """
    Endpoint to stream notifications for toxic comments.
    """
    async def event_stream():
        while True:
            # Wait for a notification from the queue
            notification = await notification_queue.get()
            yield f"data: {notification}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/articles/")
async def read_articles(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    """
    Endpoint to retrieve a list of articles.
    - `skip`: Number of articles to skip (for pagination).
    - `limit`: Maximum number of articles to return.
    """
    articles = await get_articles(db, skip=skip, limit=limit)
    return {"articles": articles}

@app.get("/comments/{id}")
async def read_comments(id: int, db: AsyncSession = Depends(get_db)):
    """
    Endpoint to retrieve comments for a specific article by its ID.
    - `id`: The ID of the article whose comments are being fetched.
    """
    # Fetch the article from the database
    article = await db.get(models.Article, id)
    
    # If article does not exist, return a 404 error
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Fetch comments for the article
    comments = await get_comments_article(db, id)
    
    return {"article_id": id, "comments": comments}


