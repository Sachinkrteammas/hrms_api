from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class VerificationStatus(Base):
    __tablename__ = "verification_status"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    name = Column(String(100), unique=True)

    candidates = relationship("Candidate", back_populates="verification_status")

class ReportIdentity(Base):
    __tablename__ = "report_identity"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_shadowed = Column(Boolean, default=False)
    candidate_id = Column(Integer, ForeignKey("candidate.id"), unique=True)
    pan_verified = Column(Boolean, default=False, nullable=True)
    aadhar_verified = Column(Boolean, default=False, nullable=True)
    name_verified = Column(Boolean, default=False, nullable=True)
    father_name_verified = Column(Boolean, default=False, nullable=True)
    dob_verified = Column(Boolean, default=False, nullable=True)
    gender_verified = Column(Boolean, default=False, nullable=True)
    permanent_address_score = Column(Integer, default=0, nullable=True)
    current_address_score = Column(Integer, default=0, nullable=True)
    apis = Column(JSON, nullable=True)
    score = Column(Integer, nullable=True)

    candidate = relationship("Candidate", back_populates="report_identity", uselist=False)

class ReportEmployment(Base):
    __tablename__ = "report_employment"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_shadowed = Column(Boolean, default=False)
    candidate_id = Column(Integer, ForeignKey("candidate.id"), unique=True)
    apis = Column(JSON, nullable=True)
    data = Column(JSON, nullable=True)

    candidate = relationship("Candidate", back_populates="report_employment", uselist=False)

class ReportCourtCheck(Base):
    __tablename__ = "report_court_check"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_shadowed = Column(Boolean, default=False)
    candidate_id = Column(Integer, ForeignKey("candidate.id"), unique=True)
    apis = Column(JSON, nullable=True)
    data = Column(JSON, nullable=True)
    score = Column(Integer, nullable=True)

    candidate = relationship("Candidate", back_populates="report_court_check", uselist=False)

class ReportAml(Base):
    __tablename__ = "report_aml"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_shadowed = Column(Boolean, default=False)
    candidate_id = Column(Integer, ForeignKey("candidate.id"), unique=True)
    apis = Column(JSON, nullable=True)
    data = Column(JSON, nullable=True)
    score = Column(Integer, nullable=True)

    candidate = relationship("Candidate", back_populates="report_aml", uselist=False)

class ReportBankAccount(Base):
    __tablename__ = "report_bank_account"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_shadowed = Column(Boolean, default=False)
    candidate_id = Column(Integer, ForeignKey("candidate.id"), unique=True)
    apis = Column(JSON, nullable=True)
    data = Column(JSON, nullable=True)
    score = Column(Integer, nullable=True)

    candidate = relationship("Candidate", back_populates="report_bank_account", uselist=False) 