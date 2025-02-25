import asyncio
import aiohttp
import aiomysql
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re
import pickle
from tensorflow.keras.models import load_model
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd

df = pd.read_csv('comments_data.csv')

# Load the TF-IDF vectorizer
with open('tfidf_vectorizer.pkl', 'rb') as f:
    loaded_vectorizer = pickle.load(f)


loaded_model = load_model('toxic_comment_prediction_model.h5')
class EuronewsScraper:
    def __init__(self, base_url="https://www.euronews.com/news/europe/france"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.db_config = {
            "host": "localhost",
            "user": "root",
            "password": "asus-1971",  # Ensure password security
            "db": "projdata",
        }

    async def create_connection(self):
        """Create a connection to the MySQL database."""
        try:
            return await aiomysql.connect(
                host=self.db_config["host"],
                user=self.db_config["user"],
                password=self.db_config["password"],
                db=self.db_config["db"],
            )
        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            return None

    async def fetch_page(self, session, url):
        """Fetch the content of a web page."""
        try:
            async with session.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    self.logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    def clean_text(self, text):
        """Clean and sanitize text."""
        if not text:
            return None
    
    # Remove <p> and </p> tags
        text = re.sub(r'</?p>', '', text)
    
    # Normalize spaces
        cleaned = re.sub(r'\s+', ' ', text).strip()
    
        return cleaned if cleaned else None

    async def extract_article_urls(self, html):
        """Extract article URLs from a page."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            urls = []
            big_div = soup.find("div", class_="o-block-listing__content")
            if big_div:
                articles = big_div.find_all("article", class_="m-object")
                for article in articles:
                    article_id = article.get("data-nid", "")
                    a = article.find("a", class_="m-object__title__link")
                    if a and "href" in a.attrs:
                        urls.append({
                            "url": a["href"],
                            "id": article_id
                        })
            return urls
        except Exception as e:
            self.logger.error(f"Error extracting article URLs: {e}")
            return []

    async def fetch_comments(self, session, article_id, article_url):
        """Fetch comments for an article."""
        comments_url = (
            f"https://api.vuukle.com/api/v1/Comments/loadVuukle?apiKey=1feb6d34-f2ca-4219-bff0-28be03a6d8da"
            f"&articleId={article_id}&globalRecommendation=false&host=euronews.com&start=0&uri={article_url}"
            f"&quizEnabled=false"
        )
        try:
            async with session.get(comments_url) as response:
                if response.status == 200:
                    comments_data = await response.json()
                    comments = [
                        {
                            "comment": self.clean_text(item.get("commentText", "")),
                            "user_id": item.get("userId", ""),
                            "username": self.clean_text(item.get("name", "")),
                            "timestamp": item.get("createAt", "1970-01-01 00:00:00")
                        }
                        for item in comments_data.get("data", {}).get("comments", {}).get("items", [])
                    ]
                    return comments
                else:
                    self.logger.warning(f"Failed to fetch comments: HTTP {response.status}")
                    return []
        except Exception as e:
            self.logger.error(f"Error fetching comments for {article_url}: {e}")
            return []

    async def extract_article_details(self, session, article_url, article_id):
        """Extract article details including title, summary, and comments."""
        try:
            async with session.get(f"https://www.euronews.com{article_url}",
                                   headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    article = soup.find("article", class_="o-article-newsy")
                    if not article:
                        return None

                    title_tag = article.find("h1", class_="c-article-redesign-title")
                    title = self.clean_text(title_tag.text) if title_tag else "No Title"

                    summary_tag = article.find("p", class_="c-article-summary")
                    summary = self.clean_text(summary_tag.text) if summary_tag else None

                    image_tag = article.find("img", class_="js-poster-img")
                    image = image_tag['src'] if image_tag and 'src' in image_tag.attrs else None

                    comments = await self.fetch_comments(session, article_id, article_url)

                    return {
                        "id": article_id,
                        "title": title,
                        "summary": summary,
                        "image": image,
                        "url": f"https://www.euronews.com{article_url}",
                        "comments": comments,
                        "comments_count": len(comments),
                        "scraped_at": datetime.now().isoformat()
                    }
                else:
                    self.logger.warning(f"Failed to fetch article: HTTP {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"Error scraping {article_url}: {e}")
            return None

    async def scrape_articles(self, num_pages=1):
        """Scrape articles from the Euronews website."""
        async with aiohttp.ClientSession() as session:
            articles = []
            for page in range(1, num_pages + 1):
                page_url = f"{self.base_url}?p={page}"

                html = await self.fetch_page(session, page_url)
                if not html:
                    continue

                article_urls = await self.extract_article_urls(html)

                article_tasks = [
                    self.extract_article_details(session, article['url'], article['id'])
                    for article in article_urls
                ]
                page_articles = await asyncio.gather(*article_tasks, return_exceptions=True)

                for result in page_articles:
                    if isinstance(result, dict):
                        articles.append(result)
                    elif isinstance(result, Exception):
                        self.logger.error(f"Error in scraping task: {result}")

            return articles

    async def insert_article(self, conn, article):
        async with conn.cursor() as cur:
            try:
                await cur.execute(
                """
                INSERT INTO articles (article_id, title, summary, image, scraped_at)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                summary = VALUES(summary),
                image = VALUES(image),
                scraped_at = VALUES(scraped_at);
                """,
                (article["id"], article["title"], article["summary"], article["image"], article["scraped_at"]),
                )   
                await conn.commit()
                return cur.lastrowid
            except Exception as e:
                self.logger.error(f"Error inserting article {article['id']}: {e}")
            return None

    async def insert_comments(self, conn, article_id, comments):
        async with conn.cursor() as cur:
            for comment in comments:
                
                commentt = comment["comment"]
                processed_comments = loaded_vectorizer.transform([commentt])

    # Convert sparse matrix to dense array for Keras
                processed_comments_dense = processed_comments.toarray()

    # Make predictions asynchronously
                predictions = await asyncio.to_thread(loaded_model.predict, processed_comments_dense)
                predictions = (predictions > 0.5).astype(int)
                print("aaaaaaaa ",bool(predictions))
                ans = int(predictions[0][0])
                
                try:
                    await cur.execute(
                    """
                    INSERT INTO comments (comment, username, user_id, timestamp, article_id, created_at, is_toxic)
                    VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                    ON DUPLICATE KEY UPDATE 
                    timestamp = VALUES(timestamp), 
                    is_toxic = VALUES(is_toxic);
                    """,
                    (
                        self.clean_text(comment["comment"]),
                        self.clean_text(comment["username"]),
                        comment["user_id"],
                        comment["timestamp"],
                        article_id,
                        ans
                    ),
                )
                except Exception as e:
                    self.logger.error(f"Error inserting comment for article {article_id}: {e}")
            await conn.commit()

    async def save_to_database(self, articles):
        """Save all articles and their comments to the database."""
        conn = await self.create_connection()
        if conn is None:
            return
        try:
            for article in articles:
                id = await self.insert_article(conn, article)
                await self.insert_comments(conn, id, article["comments"])
        finally:
            conn.close()

    async def continuous_scrape(self, interval=30, num_pages=6):
        """Continuously scrape the website at regular intervals."""
        try:
            while True:
                self.logger.info("Starting scraping cycle...")
                articles = await self.scrape_articles(num_pages)
                print(articles)
                await self.save_to_database(articles)
                self.logger.info("Scraping cycle completed. Waiting for next cycle...")
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            self.logger.info("Scraping stopped.")

async def main():
    """Main function to start scraping."""
    scraper = EuronewsScraper()
    await scraper.continuous_scrape()


if __name__ == "__main__":
    asyncio.run(main())
