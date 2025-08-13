from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Company(Base):
    __tablename__ = "company"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    code = Column(String(20), unique=True)
    name = Column(String(100), nullable=True)
    logo = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    gst = Column(String(20), nullable=True)
    contact_person = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    residency_no = Column(String(20), nullable=True)
    landmark = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    credits = Column(Integer, default=0)

    company_users = relationship("CompanyUser", back_populates="company")
    candidates = relationship("Candidate", back_populates="company")
    subscription_company = relationship("SubscriptionCompany", back_populates="company", uselist=False)
    reference_checks = relationship("CandidateReferenceCheck", back_populates="company")

class Service(Base):
    __tablename__ = "service"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_shadowed = Column(Boolean, default=False)
    name = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

class Subscription(Base):
    __tablename__ = "subscription"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_shadowed = Column(Boolean, default=False)
    name = Column(Text, nullable=True)
    services = Column(JSON, nullable=True)

    companies = relationship("SubscriptionCompany", back_populates="subscription")

class SubscriptionCompany(Base):
    __tablename__ = "subscription_company"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_shadowed = Column(Boolean, default=False)
    company_id = Column(Integer, ForeignKey("company.id"), unique=True)
    subscription_id = Column(Integer, ForeignKey("subscription.id"))

    company = relationship("Company", back_populates="subscription_company")
    subscription = relationship("Subscription", back_populates="companies") 