from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys

from app.db import engine, Base
from app.routers import users, products, depots, etageres, transfer, stock, alerts

# Create FastAPI app
app = FastAPI(
    title="Stock Management API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup with error handling
@app.on_event("startup")
async def init_db():
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("SUCCESS: Database tables created successfully")
    except Exception as e:
        print(f"ERROR: Failed to create database tables: {e}")
        print("Please check your database connection and make sure MySQL is running")
        # Don't exit, let the app start but with warning

# Include routers
app.include_router(users.router)
app.include_router(products.router)
app.include_router(depots.router)
app.include_router(etageres.router)
app.include_router(transfer.router)
app.include_router(stock.router)
app.include_router(alerts.router)

@app.get("/")
def root():
    return {
        "message": "Stock Management API",
        "version": "1.0.0",
        "endpoints": {
            "users": "/users",
            "products": "/products",
            "depots": "/depots",
            "etageres": "/etageres",
            "transfers": "/transfers",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )