from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Response, status
from starlette.responses import RedirectResponse

from app.core.deps import CurrentUser, DbSession
from app.core.security import InvalidTokenError, TokenType, decode_token
from app.core.settings import settings
from app.modules.auth import token_blacklist
from app.modules.auth.oauth import oauth
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import TokenPair, UserLogin, UserRead, UserRegister
from app.modules.auth.service import AuthError, AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, token: str, expires_at: datetime) -> None:
    max_age = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        path="/api/v1/auth",  # scoped — this cookie is only ever sent to auth endpoints
    )


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: DbSession, response: Response):
    service = AuthService(UserRepository(db))
    try:
        user = await service.register(payload)
        await db.commit()
    except AuthError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    tokens, refresh_token, expires_at = service.issue_tokens(user)
    _set_refresh_cookie(response, refresh_token, expires_at)
    return tokens


@router.post("/login", response_model=TokenPair)
async def login(payload: UserLogin, db: DbSession, response: Response):
    service = AuthService(UserRepository(db))
    try:
        user = await service.authenticate(payload)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    tokens, refresh_token, expires_at = service.issue_tokens(user)
    _set_refresh_cookie(response, refresh_token, expires_at)
    return tokens


@router.post("/refresh", response_model=TokenPair)
async def refresh(request: Request, db: DbSession, response: Response):
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    service = AuthService(UserRepository(db))
    try:
        tokens, new_refresh_token, expires_at = await service.rotate_refresh_token(raw_token)
        await db.commit()
    except AuthError as exc:
        await db.rollback()
        response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/v1/auth")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    _set_refresh_cookie(response, new_refresh_token, expires_at)
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response):
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_token:
        try:
            payload = decode_token(raw_token, TokenType.REFRESH)
            exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            await token_blacklist.revoke(payload["jti"], exp)
        except InvalidTokenError:
            pass  # already invalid — nothing to revoke
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/v1/auth")


@router.get("/me", response_model=UserRead)
async def get_me(current_user: CurrentUser):
    return current_user


@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: DbSession):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google auth failed")

    userinfo = token.get("userinfo")
    if not userinfo or not userinfo.get("email"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google profile missing email")

    service = AuthService(UserRepository(db))
    user = await service.get_or_create_google_user(
        google_id=userinfo["sub"], email=userinfo["email"], full_name=userinfo.get("name")
    )
    await db.commit()

    tokens, refresh_token, expires_at = service.issue_tokens(user)

    # Browser flow: redirect to frontend with the refresh cookie set and the
    # access token as a one-time URL fragment (never logged server-side,
    # frontend reads it once then stores in memory only).
    redirect = RedirectResponse(url=f"{settings.FRONTEND_URL}/callback#access_token={tokens.access_token}")
    _set_refresh_cookie(redirect, refresh_token, expires_at)
    return redirect
