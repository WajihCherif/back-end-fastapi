from app.db import SessionLocal
from app.services.user_service import UserService

s = SessionLocal()
svc = UserService()
users = svc.get_users(s)
print('count', len(users))
for u in users:
    print(u.id, u.username, u.email, u.role, type(u.role), u.is_active)
