from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="staff")  # superadmin, hr_admin, staff
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    department = Column(String, nullable=True)
    annual_salary = Column(Float, nullable=False)  # GBP
    hourly_rate = Column(Float, nullable=False)     # computed: salary / 52 / 37.5
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    meeting_participants = relationship("MeetingParticipant", back_populates="staff")


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    teams_meeting_id = Column(String, unique=True, index=True, nullable=True)
    session_type = Column(String, default="meeting")  # 'meeting' | 'call'
    title = Column(String, nullable=True)
    organiser_email = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    total_cost = Column(Float, nullable=True)         # GBP
    attendee_count = Column(Integer, nullable=True)
    matched_count = Column(Integer, nullable=True)    # how many matched salary DB
    unmatched_hourly_rate = Column(Float, nullable=True)  # fallback rate for unmatched
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    participants = relationship("MeetingParticipant", back_populates="meeting")


class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)  # null if unmatched
    email = Column(String, nullable=False)
    name = Column(String, nullable=True)
    hourly_rate_snapshot = Column(Float, nullable=True)  # rate at time of meeting
    cost_contribution = Column(Float, nullable=True)

    meeting = relationship("Meeting", back_populates="participants")
    staff = relationship("Staff", back_populates="meeting_participants")
