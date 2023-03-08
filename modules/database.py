import contextlib
import os
from sqlite3 import ProgrammingError
from time import sleep
from typing import List
from typing import Optional

from dotenv import load_dotenv
from pyrogram import Client
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy import select
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str]

    day: Mapped[int]
    month: Mapped[str]
    year: Mapped[int]

    tags: Mapped[list["Tag"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Post(id={self.id!r}, filename={self.filename!r}, day={self.day!r}, month={self.month!r}, year={self.year!r}, timestamp={self.timestamp!r})"


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    tag: Mapped[str]

    post_id: Mapped[int] = mapped_column(ForeignKey("post.id"))
    post: Mapped["Post"] = relationship(back_populates="tags")

    def __repr__(self) -> str:
        return f"Tag(id={self.id!r}, post_id={self.post_id!r}, tag={self.tag!r})"


engine = create_engine("sqlite+pysqlite:///posts.db", echo=True)


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
        update_DB(messages)


def update_DB(messages):
    with contextlib.suppress(FileNotFoundError, ProgrammingError):
        engine.dispose()
        sleep(5)
        os.remove("posts.db")

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        for item in messages:
            try:
                tags = item[1].split("Tags: ")[1].casefold().strip().split(",")
                tag_list = [Tag(tag=tag.strip()) for tag in tags]
            except IndexError:
                tag_list = []
            session.add(
                Post(
                    id=item[0],
                    filename=item[1].split("FileName: ")[-1].split("Taken:")[0].strip(),
                    day=(
                        item[1]
                        .split("Taken: ")[-1]
                        .split("Created:")[0]
                        .split(", ")[0]
                        .split(" ")[1]
                    ),
                    month=(
                        item[1]
                        .split("Taken: ")[-1]
                        .split("Created:")[0]
                        .split(", ")[0]
                        .split(" ")[0]
                        .casefold()
                    ),
                    year=item[1]
                    .split("Taken: ")[-1]
                    .split("Created:")[0]
                    .split(", ")[1],
                    tags=tag_list,
                )
            )
            session.commit()


def search_in_DB(search_type, value, offset=None, limit=None):
    results = []
    search_type = search_type.casefold()
    with Session(engine) as session:
        if search_type in ["id", "day", "month", "year", "date", "filename"]:
            if search_type == "id":
                result = (
                    select(Post)
                    .where(Post.id.in_([value[1]]))
                    .offset(offset)
                    .limit(limit)
                )
            if search_type == "day":
                result = (
                    select(Post)
                    .where(Post.day.in_([value[1]]))
                    .offset(offset)
                    .limit(limit)
                )
            if search_type == "month":
                result = (
                    select(Post)
                    .where(Post.month.in_([value[1].casefold()]))
                    .offset(offset)
                    .limit(limit)
                )
            if search_type == "year":
                result = (
                    select(Post)
                    .where(Post.year.in_([value[1]]))
                    .offset(offset)
                    .limit(limit)
                )
            if search_type == "date":
                result = (
                    select(Post)
                    .where(Post.day.in_([value[1]]))
                    .where(Post.month.in_([value[2].casefold()]))
                    .where(Post.year.in_([value[3]]))
                    .offset(offset)
                    .limit(limit)
                )
            if search_type == "filename":
                result = (
                    select(Post)
                    .where(Post.filename.in_([value[1]]))
                    .offset(offset)
                    .limit(limit)
                )
            results.extend((row.id, row.filename) for row in session.scalars(result))

        if search_type in ["tag", "tags", "album", "albums"]:
            result = (
                select(Tag).where(Tag.tag.in_([value[1]])).offset(offset).limit(limit)
            )
            results.extend(
                (row.post.id, row.post.filename) for row in session.scalars(result)
            )

    return results


def add_to_DB(id, filename, takentime, tags=[]):
    # sourcery skip: default-mutable-arg

    day = takentime.split(", ")[0].split(" ")[1]
    month = takentime.split(", ")[0].split(" ")[0].casefold()
    year = takentime.split(", ")[1]
    tag_list = [Tag(tag=tag.strip()) for tag in tags]

    with Session(engine) as session:
        session.add(
            Post(
                id=id, filename=filename, day=day, month=month, year=year, tags=tag_list
            )
        )
        session.commit()


def remove_from_DB(value):
    with Session(engine) as session:
        post = session.get(Post, value)
        session.delete(post)
        session.commit()
    return post
