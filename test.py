import pickle
from tensorflow.keras.models import load_model
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd

# Load the data
df = pd.read_csv('comments_data.csv')

# Load the TF-IDF vectorizer
with open('tfidf_vectorizer.pkl', 'rb') as f:
    loaded_vectorizer = pickle.load(f)

# Load the trained model
loaded_model = load_model('toxic_comment_prediction_model.h5')

# Select comments (rows 1-5 in the DataFrame)
# Using iloc[1:6] gives rows 1-5 (zero-based indexing)
comments = [
    "muslims are extrimists",
    "You are great"
]  # .values converts to numpy array

# Process multiple comments
processed_comments = loaded_vectorizer.transform(comments)

# Convert sparse matrix to dense array for Keras
processed_comments_dense = processed_comments.toarray()

# Make predictions
predictions = (loaded_model.predict(processed_comments_dense) > 0.5).astype(int)

# Print comments and their corresponding predictions
for comment, prediction in zip(comments, predictions):
    print("Comment:", comment)
    print("Prediction:", prediction)
    print("-" * 50)