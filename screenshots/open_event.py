import sys
sys.path.insert(0, 'backend')
from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    db.execute(text("UPDATE events SET event_status='open', opened_at=NOW() WHERE event_id=1"))
    db.commit()
    print("Event 1 set to open")
    
    r = db.execute(text("SELECT event_id, event_code, event_status, event_title FROM events WHERE event_id=1")).fetchone()
    print(f"ID={r[0]} Code={r[1]} Status={r[2]} Title={r[3]}")
finally:
    db.close()
