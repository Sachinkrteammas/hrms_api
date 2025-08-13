from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import os

from routers import auth, candidate, company, admin, common
from models.database import engine, Base
from config import settings

# Create uploads directory if it doesn't exist
if not os.path.exists("uploads"):
    os.makedirs("uploads")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting HRMS FastAPI application...")
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    print("Shutting down HRMS FastAPI application...")

app = FastAPI(
    title="HRMS API",
    description="HRMS Background Verification System API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure this properly for production
)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/accounts", tags=["Authentication"])
app.include_router(candidate.router, prefix="/candidate", tags=["Candidates"])
app.include_router(company.router, prefix="/company", tags=["Companies"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(common.router, prefix="/common", tags=["Common"])

@app.get("/")
async def root():
    return {
        "message": "HRMS API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info"
    )