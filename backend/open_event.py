import os
os.chdir(os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    r = db.execute(text("SELECT event_id, event_code, event_status, event_title FROM events ORDER BY event_id LIMIT 5")).fetchall()
    for x in r:
        print(f"{x[0]} {x[1]} {x[2]} {x[3]}")
    
    db.execute(text("UPDATE events SET event_status='open', opened_at=NOW() WHERE event_id=1"))
    db.commit()
    print("Event 1 set to open")
finally:
    db.close()
