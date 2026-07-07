import os
from sqlalchemy import text
from app.ai.llm import get_embedding, EMBEDDING_DIMENSIONS


def search_similar(db, query, user_id):
    embedding = get_embedding(query)
    vector_str = "ARRAY[" + ", ".join(str(float(x)) for x in embedding) + "]::vector"

    result = db.execute(
        text(
            """
            SELECT text
            FROM tasks
            WHERE user_id = :user_id
            ORDER BY embedding <-> """
            + vector_str
            + """
            LIMIT 3
            """
        ),
        {"user_id": user_id},
    )

    return result.fetchall()
