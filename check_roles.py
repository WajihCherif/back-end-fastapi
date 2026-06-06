from app.db import engine
from sqlalchemy import text
with engine.connect() as conn:
    res = conn.execute(text("SELECT DISTINCT role FROM users"))
    print([r[0] for r in res])
