from app.db import engine
from sqlalchemy import text

print('Starting role enum migration v2...')
with engine.connect() as conn:
    try:
        print('Altering role column to VARCHAR(50)')
        conn.execute(text("ALTER TABLE users MODIFY COLUMN role VARCHAR(50)"))
        conn.commit()
        print('Updating existing role values to lowercase mapping...')
        conn.execute(text("UPDATE users SET role = 'admin' WHERE role = 'ADMIN'"))
        conn.execute(text("UPDATE users SET role = 'responsible' WHERE role IN ('MANAGER','MANAGER ', 'Manager')"))
        conn.commit()
        print('Altering column to ENUM(\'admin\', \'responsible\')...')
        conn.execute(text("ALTER TABLE users MODIFY COLUMN role ENUM('admin','responsible') NOT NULL DEFAULT 'responsible'"))
        conn.commit()
        print('Migration v2 complete.')
    except Exception as e:
        print('Migration v2 error:', e)
        conn.rollback()
