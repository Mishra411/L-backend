from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Enum as SQLAEnum
from sqlalchemy.sql import func
from .database import Base
import uuid
from enum import Enum
# ADDED: import hashlib
import hashlib
from sqlalchemy import Column, Integer, String
# Removed: from .database import Base (duplicate)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)  # 'admin' or 'user'

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

    def verify_password(self, pwd: str):
        # hashlib import added above
        return hashlib.sha256(pwd.encode("utf-8")).hexdigest() == self.password

def gen_uuid():
    return str(uuid.uuid4())

# ... (rest of the file is unchanged)

class UrgencyLevel(str, Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"
    Critical = "Critical"

class ReportStatus(str, Enum):
    Submitted = "Submitted"
    InProgress = "In Progress"
    Resolved = "Resolved"

class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=gen_uuid)
    station_name = Column(String, nullable=False, index=True)
    station_city = Column(String, nullable=False, index=True)
    issue_category = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    photo_url = Column(String, nullable=True)
    urgency_level = Column(SQLAEnum(UrgencyLevel), nullable=False, default=UrgencyLevel.Medium)
    status = Column(SQLAEnum(ReportStatus), nullable=False, default=ReportStatus.Submitted)
    inspector_notes = Column(Text, nullable=True)
    reporter_contact = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_by = Column(String, nullable=True)
    ai_analysis = Column(Text, nullable=True)
