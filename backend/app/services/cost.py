from typing import List, Tuple
from sqlalchemy.orm import Session
from ..models.models import Staff, Meeting, MeetingParticipant
from datetime import datetime


WORKING_HOURS_PER_YEAR = 52 * 37.5  # 1950 hours


def compute_hourly_rate(annual_salary: float) -> float:
    return round(annual_salary / WORKING_HOURS_PER_YEAR, 4)


def match_attendees(db: Session, emails: List[str]) -> Tuple[List[Staff], List[str]]:
    """Match emails to staff records. Returns (matched_staff, unmatched_emails)."""
    emails_lower = [e.lower().strip() for e in emails]
    matched = db.query(Staff).filter(
        Staff.email.in_(emails_lower),
        Staff.is_active == True
    ).all()
    matched_emails = {s.email.lower() for s in matched}
    unmatched = [e for e in emails_lower if e not in matched_emails]
    return matched, unmatched


def calculate_cost(hourly_rate: float, duration_seconds: int) -> float:
    """Calculate cost for a given hourly rate and duration."""
    return round(hourly_rate * (duration_seconds / 3600), 4)


def start_meeting(
    db: Session,
    teams_meeting_id: str,
    title: str,
    organiser_email: str,
    attendee_emails: List[str],
    session_type: str = "meeting",
    unmatched_hourly_rate: float = None
) -> dict:
    matched_staff, unmatched = match_attendees(db, attendee_emails)
    matched_hourly = sum(s.hourly_rate for s in matched_staff)

    # For call mode: apply fallback rate to unmatched attendees
    fallback_rate = unmatched_hourly_rate or 0
    unmatched_total_hourly = fallback_rate * len(unmatched)
    total_hourly_rate = matched_hourly + unmatched_total_hourly

    meeting = Meeting(
        teams_meeting_id=teams_meeting_id,
        session_type=session_type,
        title=title,
        organiser_email=organiser_email,
        started_at=datetime.utcnow(),
        attendee_count=len(attendee_emails),
        matched_count=len(matched_staff),
        unmatched_hourly_rate=fallback_rate if unmatched else None,
    )
    db.add(meeting)
    db.flush()

    for staff in matched_staff:
        participant = MeetingParticipant(
            meeting_id=meeting.id,
            staff_id=staff.id,
            email=staff.email,
            name=staff.name,
            hourly_rate_snapshot=staff.hourly_rate,
        )
        db.add(participant)

    for email in unmatched:
        participant = MeetingParticipant(
            meeting_id=meeting.id,
            email=email,
            hourly_rate_snapshot=fallback_rate if fallback_rate else None,
        )
        db.add(participant)

    db.commit()
    db.refresh(meeting)

    return {
        "meeting_id": meeting.id,
        "total_hourly_rate": total_hourly_rate,
        "matched_count": len(matched_staff),
        "attendee_count": len(attendee_emails),
        "unmatched_emails": unmatched,
        "unmatched_count": len(unmatched),
        "fallback_rate_applied": fallback_rate > 0 and len(unmatched) > 0,
    }


def end_meeting(db: Session, meeting_id: int, duration_seconds: int) -> Meeting:
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        return None

    participants = db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting_id,
        MeetingParticipant.hourly_rate_snapshot != None
    ).all()

    total_cost = 0
    for p in participants:
        cost = calculate_cost(p.hourly_rate_snapshot, duration_seconds)
        p.cost_contribution = cost
        total_cost += cost

    meeting.ended_at = datetime.utcnow()
    meeting.duration_seconds = duration_seconds
    meeting.total_cost = round(total_cost, 2)

    db.commit()
    db.refresh(meeting)
    return meeting
