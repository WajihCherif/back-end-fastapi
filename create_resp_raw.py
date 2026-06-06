from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("INSERT INTO users (username, email, password_hash, full_name, role, is_active) VALUES ('resp_raw', 'resp_raw@example.com', 'RespRaw123', 'Responsible Raw', 'responsible', 1)"))
        conn.commit()
        print('Inserted resp_raw user')
    except Exception as e:
        print('Error inserting raw user:', e)
