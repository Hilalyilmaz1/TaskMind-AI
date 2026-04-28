from datetime import datetime, timedelta
from jose import jwt 
from passlib.context import CryptContext

SECRET_KEY="secret123"
ALGORITHM="HS256"

pwd_context=CryptContext(schemes=["pbkdf2_sha256"],deprecated="auto")

def hash_password(password:str):
    return pwd_context.hash(password)

def verify_password(plain,hashed):
    return pwd_context.verify(plain,hashed)

def create_token(data:dict):
    to_encode=data.copy()
    expire=datetime.utcnow()+timedelta(hours=2)
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode,SECRET_KEY, algorithm=ALGORITHM)