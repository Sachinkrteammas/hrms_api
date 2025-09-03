from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum

class ReferenceCheckStatus(enum.Enum):
    PENDING = "PENDING"
    REQUESTED = "REQUESTED"
    SUBMITTED = "SUBMITTED"

class CandidateReferenceCheck(Base):
    __tablename__ = "candidate_reference_check"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_shadowed = Column(Boolean, default=False)
    candidate_id = Column(Integer, ForeignKey("candidate.id"))
    company_id = Column(Integer, ForeignKey("company.id"))
    status = Column(Enum(ReferenceCheckStatus), default=ReferenceCheckStatus.PENDING)
    reference_name = Column(String(100))
    reference_email = Column(String(100))
    reference_phone = Column(String(20), nullable=True)
    reference_designation = Column(String(100), nullable=True)
    candidate_doj = Column(String(20), nullable=True)  # Date of joining
    candidate_lwd = Column(String(20), nullable=True)  # Last working day
    candidate_leaving_reason = Column(Text, nullable=True)
    candidate_strengths = Column(Text, nullable=True)
    candidate_improvements = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)
    last_ctc = Column(String(50), nullable=True)
    rehire = Column(Boolean, default=False)
    data = Column(Text, nullable=True)

    candidate = relationship("Candidate", back_populates="reference_checks")
    company = relationship("Company", back_populates="reference_checks") 