from sqlalchemy import Column, String, Boolean, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid

# Association table for User-Role M2M
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_name", String(50), ForeignKey("roles.name", ondelete="CASCADE"), primary_key=True)
)

class Role(Base):
    __tablename__ = "roles"

    name = Column(String(50), primary_key=True)
    description = Column(String(255), nullable=True)

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=True)
    school_id = Column(String(100), index=True, nullable=True)
    # Teacher's chosen target/mother-tongue language for the classroom UI
    # (ISO 639-3: sat, unr, hoc...). Defaults to Santali, the primary pilot
    # language; the mobile app lets the teacher change it via PATCH /auth/me.
    preferred_language = Column(String(10), nullable=False, default="sat")
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    roles = relationship("Role", secondary=user_roles, lazy="joined")
    audit_logs = relationship("AuditLog", back_populates="user")

class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), index=True, nullable=False)
    resource_type = Column(String(50), index=True, nullable=False)
    resource_id = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)

    user = relationship("User", back_populates="audit_logs")
