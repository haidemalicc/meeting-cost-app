from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import User
from ..schemas.schemas import Token, LoginRequest
from ..services.auth import verify_password, create_access_token, hash_password, require_superadmin

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token({"sub": user.email, "role": user.role})
    return Token(access_token=token, token_type="bearer", role=user.role, name=user.name)


@router.post("/create-user")
def create_user(
    email: str,
    name: str,
    password: str,
    role: str = "staff",
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin)
):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=email,
        name=name,
        hashed_password=hash_password(password),
        role=role
    )
    db.add(user)
    db.commit()
    return {"message": f"User {email} created with role {role}"}
