from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
import os
from dotenv import load_dotenv

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate

load_dotenv()

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

class UserService:
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    # CRUD Operations
    
    def get_user(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    def get_users(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[User]:
        """Get all users with pagination and search"""
        query = db.query(User)
        
        if search:
            query = query.filter(
                or_(
                    User.username.contains(search),
                    User.email.contains(search),
                    User.full_name.contains(search)
                )
            )
        
        return query.offset(skip).limit(limit).all()
    
    def create_user(self, db: Session, user: UserCreate) -> User:
        """Create a new user with plain text password"""
        # Check if user exists
        existing_user = self.get_user_by_username(db, user.username)
        if existing_user:
            raise ValueError("Username already registered")
        
        existing_email = self.get_user_by_email(db, user.email)
        if existing_email:
            raise ValueError("Email already registered")
        
        # Create new user - Store plain text password
        db_user = User(
            username=user.username,
            email=user.email,
            password_hash=user.password,  # Plain text storage
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    def update_user(
        self, 
        db: Session, 
        user_id: int, 
        user_update: UserUpdate
    ) -> Optional[User]:
        """Update an existing user"""
        db_user = self.get_user(db, user_id)
        if not db_user:
            return None
        
        # Update fields
        update_data = user_update.model_dump(exclude_unset=True)
        
        if "password" in update_data and update_data["password"]:
            update_data["password_hash"] = update_data.pop("password")  # Plain text
        
        for field, value in update_data.items():
            if hasattr(db_user, field):
                setattr(db_user, field, value)
        
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    def delete_user(self, db: Session, user_id: int) -> bool:
        """Delete a user"""
        db_user = self.get_user(db, user_id)
        if not db_user:
            return False
        
        db.delete(db_user)
        db.commit()
        
        return True
    
    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate user with plain text password"""
        user = self.get_user_by_username(db, username)
        if not user:
            return None
        
        # Direct comparison for plain text passwords
        if user.password_hash != password:
            return None
        
        if not user.is_active:
            return None
        
        # Update last login
        user.last_login = datetime.now()
        db.commit()
        
        return user
    
    def update_last_login(self, db: Session, user_id: int) -> None:
        """Update user's last login timestamp"""
        user = self.get_user(db, user_id)
        if user:
            user.last_login = datetime.now()
            db.commit()