from app.db import SessionLocal
from app.models.user import User

db = SessionLocal()
try:
    users = db.query(User).filter(User.username.in_(['admin','resp'])).all()
    for u in users:
        print(u.username, u.email, u.role)
finally:
    db.close()
