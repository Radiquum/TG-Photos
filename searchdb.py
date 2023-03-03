from sqlalchemy import create_engine
from sqlalchemy import text
engine = create_engine("sqlite+pysqlite:///posts.db", echo=True)

def searchDB(search_type, value):
    results = []
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT postId FROM posts WHERE {search_type} == :{search_type}"), {search_type: value})
        for row in result:
            results.append(row.postId)
    return(results)

def searchDBlist(search_type, value, offset):
    results = []
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT fileName FROM posts WHERE {search_type} == :{search_type} LIMIT 6 OFFSET {offset}"), {search_type: value})
        for row in result:
            results.append(row.fileName)
    return(results)

def searchMedia(search_type, value):
    results = []
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT postId, fileName FROM posts WHERE {search_type} == :{search_type}"), {search_type: value})
        for row in result:
            results.append(row.postId)
    return(results)