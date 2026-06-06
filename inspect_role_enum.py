from app.db import engine
from sqlalchemy import text
with engine.connect() as conn:
    res = conn.execute(text("SELECT COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='users' AND COLUMN_NAME='role'"))
    for row in res:
        print('COLUMN_TYPE:', row[0])
