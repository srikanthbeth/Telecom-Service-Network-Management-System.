from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.auth_token import AuthToken


class AuthTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        token: str,
        token_type: str,
        expires_at: datetime,
    ) -> AuthToken:
        auth_token = AuthToken(
            user_id=user_id,
            token=token,
            token_type=token_type,
            expires_at=expires_at,
            is_revoked=False,
        )

        self.db.add(auth_token)
        self.db.commit()
        self.db.refresh(auth_token)

        return auth_token

    def get_valid_token(
        self,
        token: str,
        token_type: str,
    ) -> AuthToken | None:
        statement = select(AuthToken).where(
            AuthToken.token == token,
            AuthToken.token_type == token_type,
            AuthToken.is_revoked.is_(False),
        )

        auth_token = self.db.scalar(statement)

        if not auth_token:
            return None

        now = datetime.now(timezone.utc)

        expires_at = auth_token.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= now:
            return None

        return auth_token

    def revoke(self, token: str) -> None:
        statement = select(AuthToken).where(
            AuthToken.token == token,
        )

        auth_token = self.db.scalar(statement)

        if auth_token:
            auth_token.is_revoked = True
            self.db.commit()

    def revoke_all_for_user(
        self,
        user_id: int,
        token_type: str | None = None,
    ) -> None:
        statement = select(AuthToken).where(
            AuthToken.user_id == user_id,
            AuthToken.is_revoked.is_(False),
        )

        if token_type:
            statement = statement.where(
                AuthToken.token_type == token_type
            )

        tokens = self.db.scalars(statement).all()

        for token in tokens:
            token.is_revoked = True

        self.db.commit()