from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from datetime import datetime

from models.database import get_db
from models.verification import VerificationStatus
from schemas.common import BaseResponse

router = APIRouter()

@router.get("/verification-statuses")
async def get_verification_statuses(
    db: Session = Depends(get_db)
):
    """Get all verification statuses"""
    statuses = db.query(VerificationStatus).all()
    return [{"id": status.id, "name": status.name} for status in statuses]

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...)
):
    """Upload file endpoint"""
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads"
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "message": "File uploaded successfully",
            "filename": unique_filename,
            "original_name": file.filename,
            "url": f"/uploads/{unique_filename}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"} 