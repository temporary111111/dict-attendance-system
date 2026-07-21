import sys
sys.path.insert(0, 'backend')
from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    rows = db.execute(text("SELECT event_id, event_code, event_status, event_title FROM events ORDER BY event_id LIMIT 10")).fetchall()
    for r in rows:
        print(f"ID={r[0]} Code={r[1]} Status={r[2]} Title={r[3]}")
finally:
    db.close()
