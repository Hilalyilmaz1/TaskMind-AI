from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from app.db import SessionLocal
from app.models import Task
from app.notification import send_telegram

scheduler = BackgroundScheduler(daemon=False)


def check_tasks():
    print("⏳ Scheduler çalıştı", flush=True)
    db = None
    try:
        db = SessionLocal()

        now = datetime.now()
        upcoming = now + timedelta(minutes=10)

        tasks = db.query(Task).filter(
            Task.due_date != None
        ).all()

        print(f"Scheduler: {len(tasks)} görev yüklendi", flush=True)

        for task in tasks:
            if not task.due_date:
                continue

            time_to_due = (task.due_date - now).total_seconds()
            print(
                f"Task kontrolü: {task.text} | due_date={task.due_date} | kalan={time_to_due/60:.1f} dk",
                flush=True,
            )

            if 0 <= time_to_due <= 600:
                reminder_msg = f"🔔 HATIRLATMA: {task.text} - {task.due_date}"
                print(reminder_msg, flush=True)
                try:
                    send_telegram(reminder_msg)
                except Exception as e:
                    print(f"Telegram hatası: {e}", flush=True)
    except Exception as e:
        print(f"Scheduler hata: {e}", flush=True)
        if db is not None:
            db.rollback()
    finally:
        if db is not None:
            db.close()


def start_scheduler():
    if scheduler.running:
        return

    if scheduler.get_job("check_tasks") is None:
        scheduler.add_job(
            check_tasks,
            trigger="interval",
            minutes=1,
            next_run_time=datetime.now(),
            id="check_tasks",
            coalesce=True,
            misfire_grace_time=120,
            max_instances=1,
        )
    scheduler.start()
