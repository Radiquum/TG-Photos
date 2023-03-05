## Imports ##
# Enviroment #
from dotenv import load_dotenv

load_dotenv()

# System #

import time
import os

# DataBase #

from sqlalchemy import create_engine
from sqlalchemy import text

# Scraper #

import snscrape.modules.telegram as sntelegram

## Functions ##

engine = create_engine("sqlite+pysqlite:///posts.db", echo=True)


def update_DataBase():
    try:
        os.remove("posts.db")
    except FileNotFoundError:
        pass

    with engine.connect() as conn:
        conn.execute(
            text(
                "CREATE TABLE posts (postId int, fileName str, tags str, day str, month str, year str, timestamp float)"
            )
        )
        # conn.execute(text("CREATE TABLE tags (postId int, fileName str, tags str, day str, month str, year str, timestamp float)"))
        for item in sntelegram.TelegramChannelScraper(
            os.getenv("chatLink")
        ).get_items():
            postId = item.url.split("/")[-1]
            try:
                day = (
                    item.content.split("Taken: ")[-1]
                    .split("Created:")[0]
                    .split(", ")[0]
                    .split(" ")[1]
                )
                month = (
                    item.content.split("Taken: ")[-1]
                    .split("Created:")[0]
                    .split(", ")[0]
                    .split(" ")[0]
                )
                year = (
                    item.content.split("Taken: ")[-1]
                    .split("Created:")[0]
                    .split(", ")[1]
                )
                timestamp = time.mktime(
                    time.strptime(f"{month} {day} {year}", "%b %d %Y")
                )
                fileName = (
                    item.content.split("FileName: ")[-1].split("Taken:")[0].strip()
                )
            except (ValueError, IndexError):
                continue
            conn.execute(
                text(
                    "INSERT INTO posts (postId, fileName, day, month, year, timestamp) VALUES (:postId, :fileName, :day, :month, :year, :timestamp)"
                ),
                [
                    {
                        "postId": postId,
                        "fileName": fileName,
                        "day": day,
                        "month": month,
                        "year": year,
                        "timestamp": timestamp,
                    }
                ],
            )
            conn.commit()

        result = conn.execute(text("SELECT postId, timestamp FROM posts"))
        for row in result:
            print(f"postId: {row.postId}  timestamp: {row.timestamp}")
        print("done")


def searchDB(search_type, value):
    results = []
    with engine.connect() as conn:
        result = conn.execute(
            text(f"SELECT postId FROM posts WHERE {search_type} == :{search_type}"),
            {search_type: value},
        )
        results.extend(row.postId for row in result)
    return results


def searchDBlist(search_type, value, offset=0, limit=6):
    results = []
    with engine.connect() as conn:
        result = conn.execute(
            text(
                f"SELECT postId, fileName FROM posts WHERE {search_type} == :{search_type} LIMIT {limit} OFFSET {offset}"
            ),
            {search_type: value},
        )
        results.extend((row.fileName, row.postId) for row in result)
    return results


def add_to_DataBase(postId, fileName, takenTime, tags="NULL"):
    day = takenTime.split(", ")[0].split(" ")[1]
    month = takenTime.split(", ")[0].split(" ")[0]
    year = takenTime.split(", ")[1]
    timestamp = time.mktime(time.strptime(f"{month} {day} {year}", "%b %d %Y"))
    with engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO posts (postId, fileName, tags, day, month, year, timestamp) VALUES (:postId, :fileName, :tags, :day, :month, :year, :timestamp)"
            ),
            [
                {
                    "postId": postId,
                    "fileName": fileName,
                    "tags": tags,
                    "day": day,
                    "month": month,
                    "year": year,
                    "timestamp": timestamp,
                }
            ],
        )
        conn.commit()


def remove_from_DataBase(search_type, value):
    postId = searchDBlist(search_type, value, 0, 100)
    with engine.connect() as conn:
        conn.execute(
            text(f"DELETE FROM posts WHERE {search_type} == :{search_type}"),
            {search_type: value},
        )
        conn.commit()
    return postId


if __name__ == "__main__":
    update_DataBase()
