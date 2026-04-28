from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@pgvector_db:5432/tasks")

#engine, veritabanı bağlantısını yönetir. create_engine fonksiyonu, verilen DATABASE_URL ile bir engine oluşturur.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True  # bağlantı koparsa otomatik yeniler
)
#session oluşturmak için sessionmaker kullanılır. sessionmaker, veritabanı işlemlerini yönetmek için bir oturum sınıfı oluşturur.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
#FASTAPI için DB dependency'si oluşturulur. get_db fonksiyonu, bir veritabanı oturumu oluşturur ve kullanıldıktan sonra kapatır. Bu, her istek için yeni bir oturum sağlar ve kaynakların düzgün yönetilmesini sağlar.
def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()    

