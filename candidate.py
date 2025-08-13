# candidate.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from schemas import CandidateDTO, CandidateUpdateDTO
from services.candidate_service import CandidateService
from services.company_service import CompanyService
from dependencies.auth import (
    get_current_admin,          # 🔒 admin-level access
    get_current_candidate,      # 🔒 candidate-level access
)
from utils.encrypt import encrypt_slug
from database import get_db

router = APIRouter(prefix="/candidate", tags=["candidate"])

# ─────────────────────────────── #
#  POST /candidate   (add)        #
# ─────────────────────────────── #
@router.post("")
async def add_candidate(
    dto: CandidateDTO,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    company_id = admin.company_id
    company_service = CompanyService(db)
    candidate_service = CandidateService(db)

    credits = await company_service.get_credits(company_id)
    if not credits or credits <= 0:
        raise HTTPException(status_code=400, detail="Not enough credits.")

    candidate = await candidate_service.add_candidate(dto, company_id)

    if candidate:
        await company_service.reduce_credits(company_id, 1)
        await candidate_service.send_email_to_candidate(candidate, is_existing=False)

    return {"message": "Candidate added successfully"}


# ─────────────────────────────── #
#  GET /candidate   (list)        #
# ─────────────────────────────── #
@router.get("")
async def get_candidates(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
    limit: int = Query(10),
    next: int = Query(0),
):
    company_id = admin.company_id
    candidate_service = CandidateService(db)

    items = await candidate_service.get_candidates(company_id, limit, next)
    insights = await candidate_service.get_candidate_insights(company_id)

    return {
        "items": items,
        "insights": insights,
        "next": next + limit if len(items) == limit else -1,
    }


# ─────────────────────────────── #
#  PUT /candidate   (update)      #
# ─────────────────────────────── #
@router.put("")
async def update_candidate(
    dto: CandidateUpdateDTO,
    db: Session = Depends(get_db),
    candidate_user=Depends(get_current_candidate),
):
    candidate_service = CandidateService(db)

    candidate = await candidate_service.update_candidate(dto, candidate_user.id)

    slug = None
    if dto.verify:
        slug = encrypt_slug(str(candidate_user.id))
        await candidate_service.update_candidate_status("SUBMITTED", candidate_user.id)
        await candidate_service.verify_candidate(candidate, candidate_user.id)

    return {"message": "Candidate updated successfully", "slug": slug}


# ─────────────────────────────── #
#  REVERIFICATION ENDPOINTS       #
# ─────────────────────────────── #

@router.post("/{candidate_id}/reverify/identity")
async def revalidate_identity(
    candidate_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Revalidate candidate identity"""
    candidate_service = CandidateService(db)
    return await candidate_service.revalidate_identity(candidate_id)


@router.post("/{candidate_id}/reverify/employment")
async def revalidate_employment(
    candidate_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Revalidate candidate employment"""
    candidate_service = CandidateService(db)
    return await candidate_service.revalidate_employment(candidate_id)


@router.post("/{candidate_id}/reverify/aml")
async def revalidate_aml(
    candidate_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Revalidate candidate AML (Anti-Money Laundering)"""
    candidate_service = CandidateService(db)
    return await candidate_service.revalidate_aml(candidate_id)


@router.post("/{candidate_id}/reverify/bankAccount")
async def revalidate_bank(
    candidate_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Revalidate candidate bank account"""
    candidate_service = CandidateService(db)
    return await candidate_service.revalidate_bank(candidate_id)


@router.post("/{candidate_id}/reverify/court")
async def revalidate_court(
    candidate_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Revalidate candidate court records"""
    candidate_service = CandidateService(db)
    return await candidate_service.revalidate_court(candidate_id)


# ─────────────────────────────── #
#  BULK UPLOAD ENDPOINT           #
# ─────────────────────────────── #

@router.post("/upload")
async def create_bulk_candidate(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Create multiple candidates from uploaded file"""
    candidate_service = CandidateService(db)
    return await candidate_service.create_bulk_candidates(file)
