"""
Auth routes: register, login, refresh, me, verify-email, resend-verification, cleanup.
"""

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.user import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user, token = await service.register(
        email=data.email,
        username=data.username,
        full_name=data.full_name,
        password=data.password,
    )
    return RegisterResponse(
        user=UserResponse.model_validate(user),
        verification_token=str(token.token),
        message=(
            "User registered successfully. "
            "Please verify your email using the provided token."
        ),
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    tokens = await service.login(email=data.email, password=data.password)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    tokens = await service.refresh_token(data.refresh)
    return tokens


@router.get("/me", response_model=UserResponse)
async def me(user=Depends(get_current_user)):
    return UserResponse.model_validate(user)


@router.post("/verify-email", response_model=dict)
async def verify_email(
    data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user = await service.verify_email(str(data.token))
    return {
        "user": UserResponse.model_validate(user).model_dump(),
        "message": "Email verified successfully.",
    }


@router.post("/resend-verification", response_model=dict)
async def resend_verification(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    token = await service.resend_verification(user)
    return {
        "verification_token": str(token.token),
        "message": "Verification token resent.",
    }


@router.post("/cleanup-unverified", response_model=dict)
async def cleanup_unverified(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.user import UserService

    service = UserService(db)
    deleted_count = await service.cleanup_unverified()
    return {
        "deleted_count": deleted_count,
        "message": f"Deleted {deleted_count} unverified user(s).",
    }
