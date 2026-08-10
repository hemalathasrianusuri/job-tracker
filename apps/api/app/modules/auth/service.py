from datetime import datetime, timedelta, timezone

from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.settings import settings
from app.modules.auth import token_blacklist
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import TokenPair, UserLogin, UserRegister


class AuthError(Exception):
    """Raised for any auth failure the router should turn into a 401/409."""


class AuthService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def register(self, payload: UserRegister) -> User:
        existing = await self.repo.get_by_email(payload.email)
        if existing:
            raise AuthError("An account with this email already exists")
        return await self.repo.create(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
        )

    async def authenticate(self, payload: UserLogin) -> User:
        user = await self.repo.get_by_email(payload.email)
        if not user or not user.hashed_password:
            # Same error for "no user" and "OAuth-only user" — don't leak which
            raise AuthError("Invalid email or password")
        if not verify_password(payload.password, user.hashed_password):
            raise AuthError("Invalid email or password")
        return user

    async def get_or_create_google_user(
        self, *, google_id: str, email: str, full_name: str | None
    ) -> User:
        user = await self.repo.get_by_google_id(google_id)
        if user:
            return user

        # Account linking: if the email already exists (registered via password),
        # attach the google_id rather than creating a duplicate account.
        existing = await self.repo.get_by_email(email)
        if existing:
            existing.google_id = google_id
            await self.repo.db.flush()
            return existing

        return await self.repo.create(
            email=email, hashed_password=None, full_name=full_name, google_id=google_id
        )

    def issue_tokens(self, user: User) -> tuple[TokenPair, str, datetime]:
        """Returns (token pair for the response body, raw refresh token for the
        cookie, refresh token expiry — the router uses the expiry to set the
        cookie's Max-Age)."""
        access_token = create_access_token(str(user.id))
        refresh_token, _jti = create_refresh_token(str(user.id))
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        return TokenPair(access_token=access_token), refresh_token, expires_at

    async def rotate_refresh_token(self, raw_refresh_token: str) -> tuple[TokenPair, str, datetime]:
        try:
            payload = decode_token(raw_refresh_token, TokenType.REFRESH)
        except InvalidTokenError as exc:
            raise AuthError(str(exc)) from exc

        jti = payload["jti"]
        if await token_blacklist.is_revoked(jti):
            raise AuthError("Refresh token has been revoked")

        user_id = payload["sub"]
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise AuthError("User no longer exists")

        # Rotation: revoke the token just used so it can't be replayed, then issue a new pair.
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        await token_blacklist.revoke(jti, exp)

        return self.issue_tokens(user)
