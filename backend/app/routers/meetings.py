from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
from datetime import datetime, timedelta
from ..database import get_db
from ..models.models import Meeting, User
from ..schemas.schemas import (
    MeetingStartRequest, MeetingStartResponse,
    MeetingEndRequest, MeetingOut,
    CostCalcRequest, CostCalcResponse, DashboardStats
)
from ..services.auth import get_current_user, require_admin
from ..services.cost import start_meeting, end_meeting, match_attendees, calculate_cost

router = APIRouter(prefix="/api/meetings", tags=["meetings"])


@router.post("/start", response_model=MeetingStartResponse)
def meeting_start(
    payload: MeetingStartRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    result = start_meeting(
        db=db,
        teams_meeting_id=payload.teams_meeting_id,
        title=payload.title,
        organiser_email=payload.organiser_email,
        attendee_emails=payload.attendee_emails,
        session_type=payload.session_type or "meeting",
        unmatched_hourly_rate=payload.unmatched_hourly_rate,
    )
    return MeetingStartResponse(**result)


@router.post("/end", response_model=MeetingOut)
def meeting_end(
    payload: MeetingEndRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    meeting = end_meeting(db, payload.meeting_id, payload.duration_seconds)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.post("/calculate", response_model=CostCalcResponse)
def calculate(
    payload: CostCalcRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    matched, unmatched = match_attendees(db, payload.attendee_emails)
    total_hourly_rate = sum(s.hourly_rate for s in matched)
    total_cost = calculate_cost(total_hourly_rate, payload.duration_seconds)

    return CostCalcResponse(
        total_cost=total_cost,
        total_hourly_rate=total_hourly_rate,
        matched_count=len(matched),
        attendee_count=len(payload.attendee_emails),
        cost_per_minute=round(total_hourly_rate / 60, 4),
    )


@router.get("/", response_model=List[MeetingOut])
def list_meetings(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    return (
        db.query(Meeting)
        .order_by(desc(Meeting.started_at))
        .offset(skip).limit(limit).all()
    )


@router.get("/dashboard", response_model=DashboardStats)
def dashboard_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    total = db.query(func.count(Meeting.id)).scalar() or 0
    total_cost = db.query(func.sum(Meeting.total_cost)).scalar() or 0
    max_cost = db.query(func.max(Meeting.total_cost)).scalar()
    total_seconds = db.query(func.sum(Meeting.duration_seconds)).scalar() or 0

    week_ago = datetime.utcnow() - timedelta(days=7)
    week_meetings = db.query(func.count(Meeting.id)).filter(Meeting.started_at >= week_ago).scalar() or 0
    week_cost = db.query(func.sum(Meeting.total_cost)).filter(Meeting.started_at >= week_ago).scalar() or 0

    return DashboardStats(
        total_meetings=total,
        total_cost=round(total_cost, 2),
        avg_cost_per_meeting=round(total_cost / total, 2) if total else 0,
        most_expensive_meeting=round(max_cost, 2) if max_cost else None,
        total_hours_spent=round(total_seconds / 3600, 1),
        meetings_this_week=week_meetings,
        cost_this_week=round(week_cost or 0, 2),
    )


@router.get("/{meeting_id}", response_model=MeetingOut)
def get_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting
