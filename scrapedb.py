import time
import os

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy import text
import snscrape.modules.telegram as sntelegram

os.remove('posts.db')

engine = create_engine("sqlite+pysqlite:///posts.db", echo=True)
with engine.connect() as conn:
    conn.execute(text("CREATE TABLE posts (postId int, tags str, day str, month str, year str, timestamp float)"))
    for item in sntelegram.TelegramChannelScraper(os.getenv('chatLink')).get_items():
        postId = item.url.split("/")[-1]
        try:
            day = item.content.split("Taken: ")[-1].split("Created:")[0].split(", ")[0].split(" ")[1]
            month = item.content.split("Taken: ")[-1].split("Created:")[0].split(", ")[0].split(" ")[0]
            year = item.content.split("Taken: ")[-1].split("Created:")[0].split(", ")[1]
            timestamp = time.mktime(time.strptime(f"{month} {day} {year}", '%b %d %Y'))
        except (ValueError, IndexError):
            continue
        conn.execute(
            text("INSERT INTO posts (postId, day, month, year, timestamp) VALUES (:postId, :day, :month, :year, :timestamp)"),
            [{"postId": postId, "day": day, "month": month, "year": year, "timestamp": timestamp}],
        )
        conn.commit()

    result = conn.execute(text("SELECT postId, timestamp FROM posts"))
    for row in result:
        print(f"postId: {row.postId}  timestamp: {row.timestamp}")
    print('done')
