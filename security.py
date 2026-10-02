from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    return pwd_context.hash(password)


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    """
    Verify a plain password against its stored hash.
    """
    return pwd_context.verify(
        password,
        password_hash,
    )


def _create_token(
    user_id: int,
    token_type: str,
    expires_delta: timedelta,
    role: str | None = None,
) -> str:
    """
    Create a signed JWT token.
    """

    expire = datetime.now(
        timezone.utc
    ) + expires_delta

    payload = {
        "sub": str(user_id),
        "type": token_type,
        "jti": str(uuid4()),
        "iat": datetime.now(timezone.utc),
        "exp": expire,
    }

    if role is not None:
        payload["role"] = role

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_access_token(
    user_id: int,
    role: str,
) -> str:
    return _create_token(
        user_id=user_id,
        token_type="access",
        expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        role=role,
    )


def create_refresh_token(
    user_id: int,
) -> str:
    return _create_token(
        user_id=user_id,
        token_type="refresh",
        expires_delta=timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        ),
    )


def create_password_reset_token(
    user_id: int,
) -> str:
    return _create_token(
        user_id=user_id,
        token_type="password_reset",
        expires_delta=timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        ),
    )


def decode_token(
    token: str,
) -> dict:
    """
    Decode and validate a JWT.

    python-jose validates the signature and expiration
    using the configured secret and algorithm.
    """

    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


def get_user_id_from_token(
    token: str,
) -> int:
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise JWTError(
            "Invalid access token"
        )

    subject = payload.get("sub")

    if not subject:
        raise JWTError(
            "Invalid token subject"
        )

    try:
        return int(subject)
    except (TypeError, ValueError) as exc:
        raise JWTError(
            "Invalid token subject"
        ) from exc