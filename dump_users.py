from app.db import engine
from sqlalchemy import text
with engine.connect() as conn:
    res = conn.execute(text("SELECT id, username, email, role, password_hash, created_at, updated_at, last_login FROM users"))
    rows = res.fetchall()
    for r in rows:
        print(dict(r._mapping))
