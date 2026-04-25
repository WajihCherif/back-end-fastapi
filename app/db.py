from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import sys

# Load .env file from the parent directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Database URL - hardcode for testing if .env not loading
DATABASE_URL = os.getenv("DATABASE_URL")

# If DATABASE_URL is None or empty, use default for XAMPP
if not DATABASE_URL:
    print("WARNING: DATABASE_URL not found in .env, using default for XAMPP")
    DATABASE_URL = "mysql+pymysql://root:@localhost:3306/stock_monitoring"
    print(f"Using: {DATABASE_URL}")

print(f"Connecting to database: {DATABASE_URL.replace('://', '://***:***@') if '://' in DATABASE_URL else DATABASE_URL}")

# Create engine
try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=True,  # Set to False in production
    )
    print("SUCCESS: Database engine created successfully")
except Exception as e:
    print(f"ERROR: Failed to create database engine: {e}")
    sys.exit(1)

# Create SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()