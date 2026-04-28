from langchain_community.vectorstores import PGVector
from langchain_ollama import OllamaEmbeddings
from sqlalchemy import text
from datetime import datetime, timedelta
import os

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")

embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url=OLLAMA_URL
)

def get_embedding(text):
    return embeddings.embed_query(text)


def get_vector_store():
    return PGVector(
        connection_string="postgresql://user:password@pgvector_db:5432/tasks",
        embedding_function=embeddings,
        collection_name="tasks"
    )

def search_similar(db, query, user_id):
    embedding = get_embedding(query)
    vector_str = "ARRAY[" + ", ".join(str(float(x)) for x in embedding) + "]::vector"

    result = db.execute(
        text("""
        SELECT text
        FROM tasks
        WHERE user_id = :user_id
        ORDER BY embedding <-> """ + vector_str + """
        LIMIT 3
        """),
        {
            "user_id": user_id
        }
    )

    return result.fetchall()
