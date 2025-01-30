from datetime import datetime
from typing import List
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import tensorflow as tf
import asyncio
from .database import get_db
import pandas as pd
import pickle
from tensorflow.keras.models import load_model
from sqlalchemy.future import select
from .models import Comment, Article
from .crud import get_articles, get_comments_article
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text  # Import the text function

app = FastAPI()

# CORS settings for Angular frontend
origins = [
    "http://localhost:4200"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

active_connections: List[WebSocket] = []

# WebSocket endpoint to listen for notifications
@app.websocket("/ws/notifications/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Keep the connection open
            await asyncio.sleep(3600)  # Sleep for 1 hour, WebSocket will remain open
    except WebSocketDisconnect:
        active_connections.remove(websocket)

last_processed_comment_time = datetime.now()
print(f"Last processed time (UTC): {last_processed_comment_time}")

# Function to periodically check for new comments
async def check_new_comments():
    global last_processed_comment_time
    while True:
        # Use 'await' to handle the async generator
        async for db in get_db():  # Fetch session here with async for
            new_comments = await get_new_comments(last_processed_comment_time, db)

            if new_comments:
                for websocket in active_connections:
                    for comment in new_comments:
                        await websocket.send_text(f"New comment: {comment['comment']}")

                last_processed_comment_time = datetime.now()

        await asyncio.sleep(5)  # Poll every 5 seconds

# Fetch new comments from the database

async def get_new_comments(last_processed_time: datetime, db: AsyncSession) -> List[dict]:
    # Your datetime value (this can be dynamically assigned based on your needs)
    last_processed_time = datetime(2025, 1, 30, 21, 2, 18, 513207)

    # Wrap your SQL query with the text function
    query = text("SELECT comments.id, comments.comment, comments.username, comments.user_id, comments.timestamp, comments.article_id, comments.created_at FROM comments WHERE comments.created_at > :last_processed_time")

    # Execute the query, passing the last_processed_time as a parameter
    result = await db.execute(query, {'last_processed_time': last_processed_time})

    # Extract the rows from the result
    comments = result.fetchall()

    # Print comments for debugging
    print(f"Retrieved {len(comments)} new comments")

    # Return the comments in the desired format
    return [{"comment": comment.comment, "username": comment.username} for comment in comments]

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(check_new_comments())  # Start background task  it enters in WebSocketDisconnect 
@app.get("/articles/")
async def read_articles(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    """
    Endpoint to retrieve a list of articles.
    """
    articles = await get_articles(db, skip=skip, limit=limit)
    return {"articles": articles}

@app.get("/comments/{id}")
async def read_comments(id: int, db: AsyncSession = Depends(get_db)):
    """
    Endpoint to retrieve comments for a specific article by its ID.
    """
    article = await db.get(Article, id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    comments = await get_comments_article(db, id)
    
    return {"article_id": id, "comments": comments}
