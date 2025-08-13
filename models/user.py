from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum

class UserRole(enum.Enum):
    HR_HEAD = "HR_HEAD"
    HR = "HR"

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_shadowed = Column(Boolean, default=False)
    email = Column(String(100), unique=True, index=True)
    password = Column(String(60), nullable=True)
    access_token = Column(String(40), nullable=True)
    role = Column(Integer, ForeignKey("role.id"))
    pass_code = Column(String(6))

    role_rel = relationship("Role", back_populates="users")
    company_user = relationship("CompanyUser", back_populates="user", uselist=False)
    meta = relationship("UserMeta", back_populates="user", uselist=False)

class Role(Base):
    __tablename__ = "role"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    name = Column(String(100), unique=True)

    users = relationship("User", back_populates="role_rel")

class CompanyUser(Base):
    __tablename__ = "company_user"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    company_id = Column(Integer, ForeignKey("company.id"))
    user_id = Column(Integer, ForeignKey("user.id"), unique=True)

    company = relationship("Company", back_populates="company_users")
    user = relationship("User", back_populates="company_user")

class UserMeta(Base):
    __tablename__ = "user_meta"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    name = Column(String(100))
    user_id = Column(Integer, ForeignKey("user.id"), unique=True)

    user = relationship("User", back_populates="meta")

class UserOtp(Base):
    __tablename__ = "user_otp"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_shadowed = Column(Boolean, default=False)
    email = Column(String(20), unique=True)
    otp = Column(String(6)) 