from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class UserOut(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    username: str
    password: str


class UrgencyLevel(str, Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"
    Critical = "Critical"

class ReportStatus(str, Enum):
    Submitted = "Submitted"
    InProgress = "In Progress"
    Resolved = "Resolved"

class ReportBase(BaseModel):
    station_name: str = Field(..., example="Central")
    station_city: str = Field(..., example="Edmonton")
    issue_category: str = Field(..., example="Slippery Surface")
    description: str
    photo_url: Optional[HttpUrl] = None
    urgency_level: Optional[UrgencyLevel] = UrgencyLevel.Medium
    status: Optional[ReportStatus] = ReportStatus.Submitted
    inspector_notes: Optional[str] = None
    reporter_contact: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_by: Optional[str] = None
    ai_analysis: Optional[str] = None

class ReportCreate(ReportBase):
    pass

class ReportUpdate(BaseModel):
    status: Optional[ReportStatus] = None
    inspector_notes: Optional[str] = None

class ReportOut(ReportBase):
    id: str
    created_date: datetime

    class Config:
        orm_mode = True

class StatsOut(BaseModel):
    total: int
    by_status: Dict[str, int]
    by_urgency: Dict[str, int]
    by_category: Dict[str, int]
    by_city: Dict[str, int]
    top_stations: List[Dict[str, str]]
