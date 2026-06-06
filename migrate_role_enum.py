from app.db import engine
from sqlalchemy import text

print('Starting role enum migration...')
with engine.connect() as conn:
    try:
        print('Updating existing role values...')
        conn.execute(text("UPDATE users SET role = 'admin' WHERE role = 'ADMIN'"))
        conn.execute(text("UPDATE users SET role = 'responsible' WHERE role IN ('MANAGER','MANAGER ' , 'Manager')"))
        conn.commit()
        print('Altering column to ENUM(\'admin\', \'responsible\')...')
        conn.execute(text("ALTER TABLE users MODIFY COLUMN role ENUM('admin','responsible') NOT NULL DEFAULT 'responsible'"))
        conn.commit()
        print('Migration complete.')
    except Exception as e:
        print('Migration error:', e)
        conn.rollback()
