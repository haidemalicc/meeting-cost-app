from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.models import Staff, User
from ..schemas.schemas import StaffCreate, StaffUpdate, StaffOut
from ..services.auth import require_admin
from ..services.cost import compute_hourly_rate

router = APIRouter(prefix="/api/staff", tags=["staff"])


@router.get("/", response_model=List[StaffOut])
def list_staff(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    return db.query(Staff).order_by(Staff.name).all()


@router.post("/", response_model=StaffOut)
def create_staff(
    payload: StaffCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    existing = db.query(Staff).filter(Staff.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Staff member with this email already exists")

    staff = Staff(
        email=payload.email.lower().strip(),
        name=payload.name,
        department=payload.department,
        annual_salary=payload.annual_salary,
        hourly_rate=compute_hourly_rate(payload.annual_salary),
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff


@router.put("/{staff_id}", response_model=StaffOut)
def update_staff(
    staff_id: int,
    payload: StaffUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    if payload.name is not None:
        staff.name = payload.name
    if payload.department is not None:
        staff.department = payload.department
    if payload.annual_salary is not None:
        staff.annual_salary = payload.annual_salary
        staff.hourly_rate = compute_hourly_rate(payload.annual_salary)
    if payload.is_active is not None:
        staff.is_active = payload.is_active

    db.commit()
    db.refresh(staff)
    return staff


@router.delete("/{staff_id}")
def delete_staff(
    staff_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    staff.is_active = False
    db.commit()
    return {"message": "Staff member deactivated"}
