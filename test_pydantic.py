from app.db import get_db
from app.services.user_service import UserService
from app.schemas.user import UserResponse
from app.db import SessionLocal

s = SessionLocal()
from app.models.user import User
orm_users = s.query(User).all()

for u in orm_users:
    try:
        ur = UserResponse.from_orm(u)
        print('OK', u.id)
    except Exception as e:
        print('ERR', u.id, type(e), e)
