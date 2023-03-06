import contextlib
import os
import time

from dotenv import load_dotenv
from pyrogram import Client
from sqlalchemy import create_engine
from sqlalchemy import text


async def fetch_messages():
    load_dotenv()
    api_id = os.getenv("appId")
    api_hash = os.getenv("appHash")
    async with Client("my_account", api_id, api_hash) as app:
        messages = []
        chat = await app.get_chat(int(os.getenv("chatId")))
        async for message in app.get_chat_history(chat_id=chat.id):
            if message.caption is None:
                continue
            messages.append((message.id, message.caption))
        update_DataBase(messages)


def update_DataBase(messages):
    with contextlib.suppress(FileNotFoundError):
        os.remove("posts.db")

    engine = create_engine("sqlite+pysqlite:///posts.db", echo=True)
    with engine.connect() as conn:
        conn.execute(
            text(
                "CREATE TABLE posts (postId int, fileName str, tags str, day str, month str, year str, timestamp float)"
            )
        )
        # conn.execute(text("CREATE TABLE tags (postId int, fileName str, tags str, day str, month str, year str, timestamp float)"))
        for item in messages:
            postId = item[0]
            try:
                day = (
                    item[1]
                    .split("Taken: ")[-1]
                    .split("Created:")[0]
                    .split(", ")[0]
                    .split(" ")[1]
                )
                month = (
                    item[1]
                    .split("Taken: ")[-1]
                    .split("Created:")[0]
                    .split(", ")[0]
                    .split(" ")[0]
                )
                year = item[1].split("Taken: ")[-1].split("Created:")[0].split(", ")[1]
                timestamp = time.mktime(
                    time.strptime(f"{month} {day} {year}", "%b %d %Y")
                )
                fileName = item[1].split("FileName: ")[-1].split("Taken:")[0].strip()
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
