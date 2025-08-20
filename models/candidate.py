from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum

class Gender(enum.Enum):
    Male = "Male"
    Female = "Female"
    Others = "Others"

class CheckStatus(enum.Enum):
    pending = "pending"
    api_failed = "api_failed"
    failed = "failed"
    verified = "verified"
    in_progress = "in_progress"

class Candidate(Base):
    __tablename__ = "candidate"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_shadowed = Column(Boolean, default=False)
    candidate_code = Column(String(36), unique=True)
    first_name = Column(String(100))
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    gender = Column(Enum(Gender), nullable=True)
    dob = Column(Date, nullable=True)
    father_name = Column(String(100), nullable=True)
    mother_name = Column(String(100), nullable=True)
    marital_status = Column(String(50), nullable=True)
    phone = Column(String(20))
    alternate_phone = Column(String(20), nullable=True)
    email = Column(String(100))
    access_token = Column(String(40), nullable=True)
    password = Column(String(60), nullable=True)
    score = Column(Integer, nullable=True)
    last_action = Column(String(100), nullable=True)
    company_id = Column(Integer, ForeignKey("company.id"))
    verification_status_id = Column(Integer, ForeignKey("verification_status.id"), nullable=True)
    image = Column(String(255), nullable=True)
    uan = Column(String(20), nullable=True)
    aadhar_address = Column(Text, nullable=True)
    aadhar_pincode = Column(Text, nullable=True)
    identity_check = Column(Enum(CheckStatus), default=CheckStatus.pending)
    employment_check = Column(Enum(CheckStatus), default=CheckStatus.pending)
    court_check = Column(Enum(CheckStatus), default=CheckStatus.pending)
    aml_check = Column(Enum(CheckStatus), default=CheckStatus.pending)
    bank_account_check = Column(Enum(CheckStatus), default=CheckStatus.pending)

    company = relationship("Company", back_populates="candidates")
    verification_status = relationship("VerificationStatus", back_populates="candidates")
    nid = relationship("CandidateNid", back_populates="candidate", uselist=False)
    address = relationship("CandidateAddress", back_populates="candidate")
    educations = relationship("CandidateEducation", back_populates="candidate")
    employments = relationship("CandidateEmployment", back_populates="candidate")
    bank_account = relationship("CandidateBankAccount", back_populates="candidate", uselist=False)
    aadhar_details = relationship("CandidateAadharDetails", back_populates="candidate", uselist=False)
    reference_checks = relationship("CandidateReferenceCheck", back_populates="candidate")
    report_identity = relationship("ReportIdentity", back_populates="candidate", uselist=False)
    report_employment = relationship("ReportEmployment", back_populates="candidate", uselist=False)
    report_court_check = relationship("ReportCourtCheck", back_populates="candidate", uselist=False)
    report_aml = relationship("ReportAml", back_populates="candidate", uselist=False)
    report_bank_account = relationship("ReportBankAccount", back_populates="candidate", uselist=False)

class CandidateNid(Base):
    __tablename__ = "candidate_nid"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_shadowed = Column(Boolean, default=False)
    candidate_id = Column(Integer, ForeignKey("candidate.id"), unique=True)
    photo = Column(String(255), nullable=True)
    aadhar = Column(String(255), nullable=True)
    pan = Column(String(255), nullable=True)
    passport = Column(String(255), nullable=True)
    aadhar_no = Column(String(20), nullable=True)
    uan_no = Column(String(20), nullable=True)
    pan_no = Column(String(20), nullable=True)
    passport_no = Column(String(20), nullable=True)

    candidate = relationship("Candidate", back_populates="nid")

class CandidateAddress(Base):
    __tablename__ = "candidate_address"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_shadowed = Column(Boolean, default=False)
    candidate_id = Column(Integer, ForeignKey("candidate.id"), unique=True)
    in_india = Column(Boolean, nullable=True)
    house_no = Column(String(100), nullable=True)
    locality = Column(String(100), nullable=True)
    residency_name = Column(String(100), nullable=True)
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(10), nullable=True)
    landmark = Column(String(100), nullable=True)
    residing_from = Column(Date, nullable=True)
    residency_proof = Column(String(255), nullable=True)
    is_current = Column(Boolean, default=False, nullable=True)

    candidate = relationship("Candidate", back_populates="address")

class CandidateAadharDetails(Base):
    __tablename__ = "candidate_aadhar_details"

    candidate_id = Column(Integer, ForeignKey("candidate.id"), primary_key=True)
    address = Column(Text, nullable=True)
    pincode = Column(Text, nullable=True)
    name = Column(Text, nullable=True)
    gender = Column(Text, nullable=True)
    dob = Column(Text, nullable=True)
    father_name = Column(Text, nullable=True)

    candidate = relationship("Candidate", back_populates="aadhar_details")

class CandidateEducation(Base):
    __tablename__ = "candidate_education"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_shadowed = Column(Boolean, default=False)
    candidate_id = Column(Integer, ForeignKey("candidate.id"))
    university = Column(String(100), nullable=True)
    degree = Column(String(100), nullable=True)
    course = Column(String(100), nullable=True)
    id_number = Column(String(50), nullable=True)
    grade = Column(String(100), nullable=True)
    college = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    mark_sheet = Column(String(255), nullable=True)
    certificate = Column(String(255), nullable=True)

    candidate = relationship("Candidate", back_populates="educations")

class CandidateEmployment(Base):
    __tablename__ = "candidate_employment"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_shadowed = Column(Boolean, default=False)
    candidate_id = Column(Integer, ForeignKey("candidate.id"))
    is_fresher = Column(Boolean, nullable=True)
    company = Column(String(100), nullable=True)
    designation = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    employee_type = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    starts_from = Column(Date, nullable=True)
    ends_at = Column(Date, nullable=True)
    currently_working = Column(Boolean, nullable=True)
    salary = Column(Float, nullable=True)
    uan = Column(String(20), nullable=True)
    employee_code = Column(String(60), nullable=True)
    band = Column(String(60), nullable=True)
    remark = Column(Text, nullable=True)
    manager = Column(Text, nullable=True)

    candidate = relationship("Candidate", back_populates="employments")

class CandidateBankAccount(Base):
    __tablename__ = "candidate_bank_account"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_shadowed = Column(Boolean, default=False)
    candidate_id = Column(Integer, ForeignKey("candidate.id"), unique=True)
    account_no = Column(String(50), nullable=True)
    ifsc = Column(String(50), nullable=True)
    name = Column(String(100), nullable=True)

    candidate = relationship("Candidate", back_populates="bank_account") 