from app.db import SessionLocal
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserRole


def main():
    db = SessionLocal()
    us = UserService()
    resp_data = {
        'username': 'resp',
        'email': 'resp@example.com',
        'password': 'RespPass123',
        'full_name': 'Responsible User',
        'role': 'responsible',
        'is_active': True
    }
    try:
        user = us.create_user(db, UserCreate(**resp_data))
        print('Created responsible user:', user.username, user.email)
    except Exception as e:
        print('Error creating responsible user:', e)
    finally:
        db.close()

if __name__ == '__main__':
    main()
