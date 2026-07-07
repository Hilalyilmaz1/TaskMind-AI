from fastapi import FastAPI, Depends, Header, Query, Request, Form, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi import Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text, or_
from jose import jwt
from datetime import datetime, timedelta
import os
import time

# Custom app modules
from app.ai.extraction import extract_task
from app.ai.time_parser import parse_datetime
from app.models import Base, Task, TaskPydantic, user
from app.db import engine, SessionLocal, get_db
from app.auth import hash_password, verify_password, create_token, SECRET_KEY, ALGORITHM
from app.ai.agent import prioritize_task
from app.scheduler import scheduler, start_scheduler
from app.ai.llm import llm
from app.ai.rag import search_similar

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class TaskCreate(BaseModel):
    text: str
    priority: int = 3
    due_date: datetime | None = None

class TaskUpdate(BaseModel):
    completed: bool


app = FastAPI(
    title="TaskMind AI",
    docs_url="/docs",
    redoc_url="/redoc"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token credentials")
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )

    db_user = db.query(user).filter(user.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return db_user


@app.get("/")
def root():
    return {"message": "API is running 🚀"}


@app.post("/task")
async def create_task(
    request: Request,
    task_data: TaskCreate | None = Body(None),
    text: str | None = Query(None),
    priority: int = Query(3, description="Task priority (1-5)"),
    due_date: str | None = Query(None, description="Due date in ISO format (YYYY-MM-DDTHH:MM:SS)"),
    user: user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if task_data is not None:
        text = task_data.text
        priority = task_data.priority
        task_due_date = task_data.due_date
    else:
        try:
            body = await request.json()
        except Exception:
            body = {}

        if not text:
            text = body.get("text")
        if body.get("priority") is not None:
            try:
                priority = int(body.get("priority", priority))
            except ValueError:
                priority = priority
        if body.get("due_date") is not None:
            due_date = body.get("due_date")

        task_due_date = None
        if due_date:
            try:
                task_due_date = datetime.fromisoformat(due_date)
            except ValueError:
                task_due_date = parse_datetime(text)

    if text is None:
        raise HTTPException(status_code=400, detail="text is required")

    print(f"DEBUG: Received text='{text}', priority={priority}, due_date='{task_due_date}'", flush=True)

    try:
        parsed = extract_task(text)
    except Exception as e:
        print(f"LLM extraction error: {e}", flush=True)
        parsed = {}

    date = parse_datetime(text)
    try:
        from app.ai.llm import get_embedding
        embedding = [float(x) for x in get_embedding(text)]
    except Exception as e:
        print(f"Embedding error: {e}", flush=True)
        embedding = [0.0] * 768  # dummy embedding fallback

    if task_due_date is None:
        task_due_date = parse_datetime(text)

    print(f"DEBUG: Final priority={priority}, due_date={task_due_date}", flush=True)

    task_obj = Task(
        text=text,
        date=date,
        priority=priority,
        description=parsed.get("description") if isinstance(parsed, dict) else None,
        embedding=embedding,
        user_id=user.id,
        due_date=task_due_date
    )

    db.add(task_obj)
    db.commit()
    db.refresh(task_obj)

    return {
        "message": "Task created",
        "task": {
            "id": task_obj.id,
            "text": task_obj.text,
            "priority": task_obj.priority,
            "due_date": str(task_obj.due_date) if task_obj.due_date else None,
        }
    }


@app.put("/task/{task_id}")
def update_task(
    task_id: int,
    request: TaskUpdate,
    user: user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task_obj = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == user.id
    ).first()

    if not task_obj:
        raise HTTPException(status_code=404, detail="Task not found")

    task_obj.completed = request.completed
    db.commit()
    db.refresh(task_obj)

    return {"message": "Task updated", "completed": task_obj.completed}


@app.get("/tasks")
def get_tasks(user: user = Depends(get_current_user), db: Session = Depends(get_db)):
    results = db.query(Task).filter(Task.user_id == user.id).all()
    return [TaskPydantic.model_validate(task) for task in results]


@app.get("/search")
def search_tasks(
    query: str = "",
    user: user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not query:
        results = db.query(Task).filter(Task.user_id == user.id).all()
    else:
        from app.ai.llm import get_embedding
        query_embedding = [float(x) for x in get_embedding(query)]

        results = db.query(Task).filter(
            Task.user_id == user.id
        ).order_by(
            Task.embedding.cosine_distance(query_embedding)
        ).limit(5).all()

    return [
        {
            "id": r.id,
            "text": r.text,
            "due_date": str(r.due_date) if r.due_date else None,
            "priority": r.priority
        }
        for r in results
    ]


@app.get("/ask")
def ask_ai(
    question: str,
    user: user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    context = ""
    try:
        # 🔍 Fetch Tasks
        if "yarın" in question.lower():
            tomorrow = datetime.now() + timedelta(days=1)
            start = tomorrow.replace(hour=0, minute=0, second=0)
            end = tomorrow.replace(hour=23, minute=59, second=59)

            tasks = db.query(Task).filter(
                Task.user_id == user.id,
                Task.due_date >= start,
                Task.due_date <= end
            ).all()

            context = "\n".join([task.text for task in tasks])
        else:
            results = search_similar(db, question, user.id)
            context = "\n".join([r[0] for r in results])

        prompt = f"""
Kullanıcı sorusu:
{question}

Bugünün tarihi:
{datetime.now()}

Kullanıcının görevleri:
{context}

Şunları yap:
1. Görevleri önceliklendir
2. Saatlere göre günlük plan oluştur
3. Çakışma varsa belirt
4. Kısa ve net yaz

Format:
- Öncelikli görevler
- Günlük plan
- Öneri
"""

        # Call the unified LLM wrapper
        if llm and llm.provider:
            answer = llm.invoke(prompt)
        else:
            answer = f"⚠️ AI model is currently offline/not configured.\n\nHere are your relevant tasks:\n{context}"

        return {"answer": answer}

    except Exception as e:
        print(f"Error in ask_ai: {e}", flush=True)
        return {
            "answer": f"⚠️ AI error occurred.\n\nRelevant tasks found:\n{context}"
        }


@app.get("/calendar")
def get_day(
    day: str,
    user: user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    normalized_day = day.strip().lower()
    if normalized_day in ["yarın", "yarin"]:
        target_date = (datetime.now() + timedelta(days=1)).date()
    else:
        try:
            if "." in day:
                target_date = datetime.strptime(day, "%d.%m.%Y").date()
            else:
                target_date = datetime.strptime(day, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid day format. Use YYYY-MM-DD, DD.MM.YYYY, or 'yarın'."
            )

    tasks = db.query(Task).filter(
        Task.user_id == user.id,
        Task.due_date.isnot(None)
    ).all()
    
    result = [
        {
            "id": t.id,
            "text": t.text,
            "due_date": str(t.due_date) if t.due_date else None,
            "priority": t.priority,
            "completed": t.completed
        }
        for t in tasks
        if t.due_date.date() == target_date
    ]
    return result


@app.post("/register")
async def register(
    request: Request,
    email: str = Form(None),
    password: str = Form(None),
    db: Session = Depends(get_db)
):
    if not email or not password:
        try:
            body = await request.json()
        except Exception:
            body = {}
        email = email or body.get("email")
        password = password or body.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="email and password required")
    
    # Check if user already exists
    existing_user = db.query(user).filter(user.email == email).first()
    if existing_user:
        return {"error": "user already exists"}

    try:
        new_user = user(
            email=email,
            password=hash_password(password)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {"message": "user created", "user_id": new_user.id}
    except Exception as e:
        db.rollback()
        return {"error": f"registration failed: {str(e)}"}


@app.post("/login")
async def login(
    request: Request,
    email: str = Form(None),
    username: str = Form(None),
    password: str = Form(None),
    db: Session = Depends(get_db)
):
    if not (email or username) or not password:
        try:
            body = await request.json()
        except Exception:
            body = {}

        email = email or body.get("email")
        username = username or body.get("username")
        password = password or body.get("password")

    login_value = email or username

    db_user = db.query(user).filter(
        user.email == login_value
    ).first()

    if not db_user or not verify_password(password, db_user.password):
        raise HTTPException(
            status_code=401,
            detail="wrong credentials"
        )

    return {
        "access_token": create_token({"user_id": db_user.id}),
        "token_type": "bearer"
    }


@app.get("/tomorrow")
def get_tomorrow_tasks(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    tomorrow = datetime.now() + timedelta(days=1)

    start = tomorrow.replace(hour=0, minute=0, second=0)
    end = tomorrow.replace(hour=23, minute=59, second=59)

    tasks = db.query(Task).filter(
        Task.due_date >= start,
        Task.due_date <= end
    ).all()

    return tasks


@app.get("/plan")
def plan_day(
    user: user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tomorrow = datetime.now() + timedelta(days=1)

    start = tomorrow.replace(hour=0, minute=0)
    end = tomorrow.replace(hour=23, minute=59)

    tasks = db.query(Task).filter(
        Task.user_id == user.id,
        Task.due_date >= start,
        Task.due_date <= end,
    ).order_by(Task.priority.asc()).all()

    context = "\n".join([
        f"{t.text} (priority {t.priority})"
        for t in tasks
    ])

    prompt = f"""
    Bu görevleri yarına planla:
    {context}

    Şunları yap:
    1. Görevleri önceliklendir
    2. Saatlere göre günlük plan oluştur
    3. Çakışma varsa belirt
    4. Kısa ve net yaz

    Format:
    - Öncelikli görevler
    - Günlük plan
    - Öneri
    """

    try:
        if llm and llm.provider:
            response = llm.invoke(prompt)
            return {"plan": response}
        else:
            return {"plan": f"Plan oluşturulamadı (AI devredışı). Görevleriniz:\n{context}"}
    except Exception as e:
        print(f"LLM error: {e}", flush=True)
        return {"plan": f"Plan oluşturulamadı: {str(e)}. Görevler: {context}"}


@app.on_event("startup")
def startup_event():
    print("🚀 Database initialization...", flush=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()

            result = conn.execute(text("SELECT to_regclass('public.tasks')")).scalar()
            if result:
                try:
                    conn.execute(text("ALTER TABLE tasks ALTER COLUMN embedding TYPE vector(768)"))
                    conn.commit()
                except Exception as e:
                    print(f"DB init warning (embedding conversion): {e}", flush=True)

                try:
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 3"))
                    conn.commit()
                except Exception as e:
                    print(f"DB init warning (priority column): {e}", flush=True)

                try:
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS date TIMESTAMP NULL"))
                    conn.commit()
                except Exception as e:
                    print(f"DB init warning (date column): {e}", flush=True)

                try:
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS due_date TIMESTAMP NULL"))
                    conn.commit()
                except Exception as e:
                    print(f"DB init warning (due_date column): {e}", flush=True)

                try:
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS completed BOOLEAN DEFAULT FALSE"))
                    conn.commit()
                except Exception:
                    try:
                        conn.execute(text("ALTER TABLE tasks ALTER COLUMN completed TYPE BOOLEAN USING (completed::boolean)"))
                        conn.commit()
                    except Exception as e:
                        print(f"DB init warning (completed column conversion): {e}", flush=True)
        
        Base.metadata.create_all(bind=engine)
        print("🚀 Database initialization complete!", flush=True)
    except Exception as e:
        print(f"⚠️ Database connection failed during startup: {e}", flush=True)
        print("FastAPI will start, but database endpoints will fail until connection is resolved.", flush=True)

    print("🚀 Scheduler başlatılıyor...", flush=True)
    start_scheduler()


@app.on_event("shutdown")
def shutdown_event():
    if scheduler.running:
        print("🛑 Scheduler kapatılıyor...", flush=True)
        scheduler.shutdown(wait=False)
