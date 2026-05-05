from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    name: str


class LoginRequest(BaseModel):
    email: str
    password: str


# --- Staff ---
class StaffCreate(BaseModel):
    email: str
    name: str
    department: Optional[str] = None
    annual_salary: float


class StaffUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    annual_salary: Optional[float] = None
    is_active: Optional[bool] = None


class StaffOut(BaseModel):
    id: int
    email: str
    name: str
    department: Optional[str]
    annual_salary: float
    hourly_rate: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Meetings ---
class MeetingStartRequest(BaseModel):
    teams_meeting_id: Optional[str] = None
    title: Optional[str] = None
    organiser_email: Optional[str] = None
    attendee_emails: List[str]
    session_type: Optional[str] = "meeting"  # 'meeting' | 'call'
    unmatched_hourly_rate: Optional[float] = None  # fallback for unmatched in call mode


class MeetingStartResponse(BaseModel):
    meeting_id: int
    total_hourly_rate: float
    matched_count: int
    attendee_count: int
    unmatched_emails: List[str]


class MeetingEndRequest(BaseModel):
    meeting_id: int
    duration_seconds: int


class ParticipantOut(BaseModel):
    email: str
    name: Optional[str]
    hourly_rate_snapshot: Optional[float]
    cost_contribution: Optional[float]

    class Config:
        from_attributes = True


class MeetingOut(BaseModel):
    id: int
    teams_meeting_id: Optional[str]
    session_type: Optional[str]
    title: Optional[str]
    organiser_email: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    total_cost: Optional[float]
    attendee_count: Optional[int]
    matched_count: Optional[int]
    unmatched_hourly_rate: Optional[float]
    participants: List[ParticipantOut] = []

    class Config:
        from_attributes = True


# --- Cost calculation ---
class CostCalcRequest(BaseModel):
    attendee_emails: List[str]
    duration_seconds: int


class CostCalcResponse(BaseModel):
    total_cost: float
    total_hourly_rate: float
    matched_count: int
    attendee_count: int
    cost_per_minute: float


# --- Dashboard stats ---
class DashboardStats(BaseModel):
    total_meetings: int
    total_cost: float
    avg_cost_per_meeting: float
    most_expensive_meeting: Optional[float]
    total_hours_spent: float
    meetings_this_week: int
    cost_this_week: float
