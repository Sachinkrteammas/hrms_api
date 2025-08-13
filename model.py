from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# --- User Table ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255), nullable=True)
    pass_code = Column(String(100))
    access_token = Column(String(255), nullable=True)
    is_admin = Column(String(1), default="N")  # Y/N for admin status
    company_id = Column(Integer, ForeignKey("company.id"), nullable=True)

    meta = relationship("UserMeta", back_populates="user", uselist=False)


# --- User Meta Table ---
class UserMeta(Base):
    __tablename__ = "user_meta"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="meta")


# --- Company Table (required for FK in CompanySubscription) ---
class Company(Base):
    __tablename__ = "company"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    credits = Column(Integer, default=0)

    subscriptions = relationship("CompanySubscription", back_populates="company")
    candidates = relationship("Candidate", back_populates="company")


# --- Company Subscription Table ---
class CompanySubscription(Base):
    __tablename__ = "company_subscription"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company.id"), nullable=False)
    subscription = Column(String(255))

    company = relationship("Company", back_populates="subscriptions")
    services = relationship("Service", back_populates="subscription")


# --- Service Table (required for FK in CompanySubscription) ---
class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    subscription_id = Column(Integer, ForeignKey("company_subscription.id"), nullable=False)

    subscription = relationship("CompanySubscription", back_populates="services")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    company_id = Column(Integer, ForeignKey("company.id"))
    status = Column(String(50), default="PENDING")
    # other fields...

    company = relationship("Company", back_populates="candidates")
