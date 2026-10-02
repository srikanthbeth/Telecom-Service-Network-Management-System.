from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session
from core.config import settings

from core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from models.user import User
from repositories.auth_token_repository import AuthTokenRepository
from repositories.user_repository import UserRepository
from schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    TokenResponse,
    UserRegister,
)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository(db)
        self.token_repository = AuthTokenRepository(db)

    def register(
        self,
        data: UserRegister,
    ) -> User:

        existing_user = self.repository.get_by_email(
            data.email
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            full_name=data.full_name,
            email=data.email.lower(),
            phone=data.phone,
            password_hash=hash_password(data.password),
            role=data.role,
            is_active=True,
            is_verified=False,
        )

        return self.repository.create(user)

    def login(
        self,
        data: LoginRequest,
    ) -> TokenResponse:

        user = self.repository.get_by_email(
            data.email
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(
            data.password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        access_token = create_access_token(
            user.id,
            user.role.value,
        )

        refresh_token = create_refresh_token(
            user.id,
        )

        refresh_expiry = datetime.now(
            timezone.utc
        ) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        self.token_repository.create(
            user_id=user.id,
            token=refresh_token,
            token_type="refresh",
            expires_at=refresh_expiry,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def refresh(
        self,
        refresh_token: str,
    ) -> TokenResponse:

        try:
            payload = decode_token(refresh_token)

            if payload.get("type") != "refresh":
                raise JWTError(
                    "Invalid refresh token"
                )

            user_id = payload.get("sub")

            if not user_id:
                raise JWTError("Missing user")

            stored_token = (
                self.token_repository.get_valid_token(
                    refresh_token,
                    "refresh",
                )
            )

            if not stored_token:
                raise JWTError(
                    "Refresh token revoked or expired"
                )

            user = self.repository.get_by_id(
                int(user_id)
            )

            if not user:
                raise JWTError("User not found")

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive",
                )

            # Revoke old refresh token
            self.token_repository.revoke(
                refresh_token
            )

            access_token = create_access_token(
                user.id,
                user.role.value,
            )

            new_refresh_token = create_refresh_token(
                user.id
            )

            refresh_expiry = datetime.now(
                timezone.utc
            ) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

            self.token_repository.create(
                user_id=user.id,
                token=new_refresh_token,
                token_type="refresh",
                expires_at=refresh_expiry,
            )

            return TokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
            )

        except HTTPException:
            raise

        except (JWTError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

    def logout(
        self,
        refresh_token: str,
    ) -> None:

        self.token_repository.revoke(
            refresh_token
        )

    def get_user(
        self,
        user_id: int,
    ) -> User:

        user = self.repository.get_by_id(
            user_id
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    def deactivate(
        self,
        user_id: int,
    ) -> User:

        user = self.get_user(user_id)

        user.is_active = False

        self.token_repository.revoke_all_for_user(
            user.id,
            "refresh",
        )

        return self.repository.update(user)

    def activate(
        self,
        user_id: int,
    ) -> User:

        user = self.get_user(user_id)

        user.is_active = True

        return self.repository.update(user)

    def create_password_reset_token(
        self,
        email: str,
    ) -> str | None:

        user = self.repository.get_by_email(
            email
        )

        if not user:
            return None

        token = create_password_reset_token(
            user.id
        )

        expires_at = datetime.now(
            timezone.utc
        ) + timedelta(minutes=30)

        self.token_repository.create(
            user_id=user.id,
            token=token,
            token_type="password_reset",
            expires_at=expires_at,
        )

        return token

    def reset_password(
        self,
        data: PasswordResetConfirm,
    ) -> None:

        try:
            payload = decode_token(
                data.token
            )

            if payload.get("type") != "password_reset":
                raise JWTError(
                    "Invalid password reset token"
                )

            user_id = payload.get("sub")

            if not user_id:
                raise JWTError(
                    "Missing user"
                )

            stored_token = (
                self.token_repository.get_valid_token(
                    data.token,
                    "password_reset",
                )
            )

            if not stored_token:
                raise JWTError(
                    "Token expired or revoked"
                )

            user = self.repository.get_by_id(
                int(user_id)
            )

            if not user:
                raise JWTError(
                    "User not found"
                )

            user.password_hash = hash_password(
                data.new_password
            )

            self.repository.update(user)

            # Reset token can only be used once
            self.token_repository.revoke(
                data.token
            )

        except (JWTError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token",
            )