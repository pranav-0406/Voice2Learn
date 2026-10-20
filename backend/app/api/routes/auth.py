"""Authentication routes for student registration, PIN login, and session tokens."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_student, get_database
from app.api.schemas import (
    AuthResponse,
    StudentLoginRequest,
    StudentProfile,
    StudentRegisterRequest,
)
from app.core.security import create_access_token, hash_pin, verify_pin
from app.db.database import Database

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_student(
    request: StudentRegisterRequest,
    database: Database = Depends(get_database),
) -> AuthResponse:
    """Register a new student profile with a secure numeric PIN."""
    existing = database.get_student_by_nickname(request.nickname)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Nickname '{request.nickname}' is already taken. Please choose another name.",
        )

    student_id = str(uuid4())
    pin_hash = hash_pin(request.pin)
    created_at = datetime.now(timezone.utc).isoformat()

    student = database.create_student(
        student_id=student_id,
        nickname=request.nickname.strip(),
        pin_hash=pin_hash,
        created_at=created_at,
        board=request.board,
        class_level=request.class_level,
        grade_band=request.grade_band,
    )

    token = create_access_token(
        {
            "sub": student_id,
            "nickname": student["nickname"],
            "grade_band": student["grade_band"],
            "class_level": student["class_level"],
        }
    )

    profile = StudentProfile(
        id=student["id"],
        nickname=student["nickname"],
        board=student["board"],
        class_level=student["class_level"],
        grade_band=student["grade_band"],
        created_at=student["created_at"],
    )

    return AuthResponse(access_token=token, token_type="bearer", student=profile)


@router.post("/login", response_model=AuthResponse)
def login_student(
    request: StudentLoginRequest,
    database: Database = Depends(get_database),
) -> AuthResponse:
    """Authenticate student using nickname and 4-digit PIN."""
    student = database.get_student_by_nickname(request.nickname)
    if not student or not verify_pin(request.pin, student.get("pin_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect nickname or PIN. Please check and try again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        {
            "sub": student["id"],
            "nickname": student["nickname"],
            "grade_band": student["grade_band"],
            "class_level": student["class_level"],
        }
    )

    profile = StudentProfile(
        id=student["id"],
        nickname=student["nickname"],
        board=student["board"],
        class_level=student["class_level"],
        grade_band=student["grade_band"],
        created_at=student["created_at"],
    )

    return AuthResponse(access_token=token, token_type="bearer", student=profile)


@router.get("/me", response_model=StudentProfile)
def get_current_profile(
    student: dict = Depends(get_current_student),
) -> StudentProfile:
    """Retrieve the currently authenticated student profile."""
    return StudentProfile(
        id=student["id"],
        nickname=student["nickname"],
        board=student["board"],
        class_level=student["class_level"],
        grade_band=student["grade_band"],
        created_at=student["created_at"],
    )
