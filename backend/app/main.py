from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .models import models  # noqa: ensure models are registered
from .routers import auth, staff, meetings
from .database import SessionLocal
from .models.models import User
from .services.auth import hash_password

app = FastAPI(
    title="Meeting Cost Calculator API",
    description="Track the real cost of your Microsoft Teams meetings",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(staff.router)
app.include_router(meetings.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    seed_superadmin()


def seed_superadmin():
    """Create default superadmin if no users exist."""
    db = SessionLocal()
    try:
        existing = db.query(User).first()
        if not existing:
            admin = User(
                email="admin@meetingcost.local",
                name="Super Admin",
                hashed_password=hash_password("admin1234"),
                role="superadmin"
            )
            db.add(admin)
            db.commit()
            print("✅ Default superadmin created: admin@meetingcost.local / admin1234")
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "Meeting Cost Calculator API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
