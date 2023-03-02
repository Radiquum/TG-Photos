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
