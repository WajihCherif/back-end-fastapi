from app.db import engine
from sqlalchemy import text

print('Starting role enum migration v3...')
with engine.connect() as conn:
    try:
        print('Altering role column to VARCHAR(50)')
        conn.execute(text("ALTER TABLE users MODIFY COLUMN role VARCHAR(50)"))
        conn.commit()
        print('Uppercasing existing role values...')
        conn.execute(text("UPDATE users SET role = UPPER(role)"))
        conn.commit()
        print('Altering column to ENUM(\'ADMIN\', \'RESPONSIBLE\')...')
        conn.execute(text("ALTER TABLE users MODIFY COLUMN role ENUM('ADMIN','RESPONSIBLE') NOT NULL DEFAULT 'RESPONSIBLE'"))
        conn.commit()
        print('Migration v3 complete.')
    except Exception as e:
        print('Migration v3 error:', e)
        conn.rollback()
