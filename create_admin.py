from app.db import SessionLocal
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserRole


def main():
    db = SessionLocal()
    us = UserService()
    admin_data = {
        'username': 'admin',
        'email': 'admin@example.com',
        'password': 'AdminPass123',
        'full_name': 'Administrator',
        'role': UserRole.ADMIN,
        'is_active': True
    }
    try:
        user = us.create_user(db, UserCreate(**admin_data))
        print('Created admin user:', user.username, user.email)
    except Exception as e:
        print('Error creating admin user:', e)
    finally:
        db.close()

if __name__ == '__main__':
    main()
