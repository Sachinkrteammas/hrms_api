# Import all models to ensure they are registered with SQLAlchemy
from .database import Base, engine, get_db
from .user import User, UserMeta, UserOtp, Role, CompanyUser
from .company import Company, Subscription, SubscriptionCompany, Service
from .candidate import (
    Candidate, CandidateNid, CandidateAddress, CandidateEducation,
    CandidateEmployment, CandidateBankAccount, CandidateAadharDetails
)
from .verification import (
    VerificationStatus, ReportIdentity, ReportEmployment,
    ReportCourtCheck, ReportAml, ReportBankAccount
)
from .reference import CandidateReferenceCheck

__all__ = [
    "Base", "engine", "get_db",
    "User", "UserMeta", "UserOtp", "Role", "CompanyUser",
    "Company", "Subscription", "SubscriptionCompany", "Service",
    "Candidate", "CandidateNid", "CandidateAddress", "CandidateEducation",
    "CandidateEmployment", "CandidateBankAccount", "CandidateAadharDetails",
    "VerificationStatus", "ReportIdentity", "ReportEmployment",
    "ReportCourtCheck", "ReportAml", "ReportBankAccount",
    "CandidateReferenceCheck"
] 