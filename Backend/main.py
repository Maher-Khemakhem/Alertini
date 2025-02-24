from collections import defaultdict
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
import json
import smtplib
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
from email.mime.multipart import MIMEMultipart
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
async def is_it_toxic(comment: CommentInput):
    """
    Endpoint to check if a comment is toxic.
    """
    # Process the comment
    comments = comment.content
    processed_comments = loaded_vectorizer.transform([comments])

    # Convert sparse matrix to dense array for Keras
    processed_comments_dense = processed_comments.toarray()

    # Make predictions asynchronously
    predictions = await asyncio.to_thread(loaded_model.predict, processed_comments_dense)
    predictions = (predictions > 0.5).astype(int)

    return bool(predictions)
active_connections: set[WebSocket] = set()
timestamp = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
processed_comments = set() 
@app.websocket("/ws/notifications/")
async def websocket_endpoint(websocket: WebSocket):
    global timestamp
    await websocket.accept()
    active_connections.add(websocket)
    timestamp = int(datetime.now(tz=timezone.utc).timestamp() * 1000)

    try:
        while True:
            data = await websocket.receive_text()  # Keep the connection alive
            print(f"Received from client: {data}") 
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print(f"Client {websocket} disconnected")
        active_connections.discard(websocket)  # Remove the disconnected client
    finally:
        if not active_connections:
            processed_comments.clear()  # Clear processed comments if no clients are connected
            print("All clients disconnected, processed_comments cleared.")



# Function to periodically check for new comments
port = 587
smtp_server = "smtp.gmail.email"
login = "maher.khemakhem@etudiant-fst.utm.tn"
password = "maherfiras"
sender_email = "maher.khemakhem@etudiant-fst.utm.tn"
to_email = "khemakhemmaher2003@gmail.com"

# Track last processed comment time
last_processed_comment_time = (datetime.now() - timedelta(days=2)).replace(second=0, microsecond=0)
print(f"Last processed time (UTC): {last_processed_comment_time}")
 # Store processed comment texts

@app.get("/send-email")
async def send_email(contenu: str):
    """ Sends an email notification. """
    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = "New Comment Notification"

    html = f"""
        <html>
        <body>
            <p>{contenu}</p>
        </body>
        </html>
    """
    part = MIMEText(html, "html")
    message.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()  # Secure connection
        server.login(login, password)
        server.sendmail(sender_email, to_email, message.as_string())
        server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")

async def check_new_comments():
    """ Periodically checks for new comments and sends notifications. """
    global last_processed_comment_time
    global timestamp
    
    while True:
        #processed_comments.clear()
        async for db in get_db():  # Fetch database session
            new_comments = await get_new_comments(last_processed_comment_time, db)
            print(new_comments)
            for comment in new_comments:
                comment_text = comment["comment"]
                
                    # Include the timestamp in the JSON message.
                message = json.dumps({
                        "message": f"New comment: {comment_text}",
                        "timestamp": timestamp
                    })
                is_toxic = comment["is_toxic"]
                #print(active_connections)
                for websocket in list(active_connections):
                        
                        if comment_text not in processed_comments and is_toxic:
                            print(comment_text)
                            await websocket.send_text(message)
                            processed_comments.add(comment_text)
                    
                            timestamp = int(datetime.now(tz=timezone.utc).timestamp() * 1000)

                    # Send email notification
                    #await send_email(comment_text)

                    # Send websocket notification
                    
                    

            # Update the timestamp after processing new comments
            last_processed_comment_time = (datetime.now() - timedelta(days=2)).replace(second=0, microsecond=0)


        await asyncio.sleep(10)  # Poll every 50 seconds
        # Fetch new comments from the database

async def get_new_comments(last_processed_time: datetime, db: AsyncSession) -> List[dict]:
    # Your datetime value (this can be dynamically assigned based on your needs)
    #last_processed_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Wrap your SQL query with the text function
    query = text("SELECT comments.id, comments.comment, comments.username, comments.user_id, comments.timestamp, comments.article_id, comments.created_at,comments.is_toxic FROM comments WHERE comments.created_at > :last_processed_time")

    # Execute the query, passing the last_processed_time as a parameter
    result = await db.execute(query, {'last_processed_time': last_processed_time})

    # Extract the rows from the result
    comments = result.fetchall()

    # Print comments for debugging
    print(f"Retrieved {len(comments)} new comments")

    # Return the comments in the desired format
    return [{"comment": comment.comment, "username": comment.username,"is_toxic":comment.is_toxic} for comment in comments]

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

@app.get("/positive-comments")
async def positive(db: AsyncSession = Depends(get_db)):
    query = text("SELECT is_toxic, DATE(created_at) FROM comments")  # Extract only date
    result = await db.execute(query)
    comments_data = result.fetchall()

    pos_counts = defaultdict(int)
    neg_counts = defaultdict(int)

    for is_toxic, date in comments_data:
        if not is_toxic:
            pos_counts[date] += 1
        else:
            neg_counts[date] += 1

    timestamps = sorted(set(pos_counts.keys()) | set(neg_counts.keys()))  # Merge unique dates

    positive_counts = [pos_counts[date] for date in timestamps]
    negative_counts = [neg_counts[date] for date in timestamps]

    return {"timestamps": timestamps, "pos": positive_counts, "neg": negative_counts}



# WebSocket endpoint to send positive comments data


@app.post("/set")
async def sett(db: AsyncSession = Depends(get_db)):
    query = text("SELECT id, comment FROM comments")  # Extract only necessary fields
    result = await db.execute(query)
    comments_data = result.fetchall()

    for id, comment in comments_data:
        if await is_it_toxic(CommentInput(content=comment)):
            update_query = text("UPDATE comments SET is_toxic=1 WHERE id=:id")
            await db.execute(update_query, {"id": id})
    
    await db.commit()  # Commit the changes to the database

