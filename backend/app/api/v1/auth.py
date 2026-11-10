import os
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.core.browser_csrf import (
    CSRF_COOKIE_NAME,
    validate_csrf_token,
)
from backend.app.core.browser_security import validate_browser_origin
from backend.app.core.cookie_settings import REFRESH_COOKIE_NAME, set_refresh_cookie
from backend.app.core.dependencies import get_current_user
from backend.app.core.security import create_access_token
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.repositories.refresh_token_repository import (
    find_refresh_token_by_hash,
)
from backend.app.repositories.user_repository import find_user_by_email
from backend.app.schemas.user import (
    TokenLogoutRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from backend.app.services.auth_service import (
    DuplicateEmailError,
    InvalidCredentialsError,
    login_user,
    register_user,
)
from backend.app.services.refresh_token_service import (
    InvalidRefreshTokenError,
    hash_refresh_token,
    issue_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: UserRegisterRequest,
    session: Annotated[Session, Depends(get_db)],
):
    try:
        return register_user(
            session=session,
            email=request.email,
            password=request.password,
        )

    except DuplicateEmailError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="회원가입 처리에 실패했습니다.",
        ) from exc


@router.post("/login", response_model=TokenResponse)
def login(
    request: UserLoginRequest,
    session: Annotated[Session, Depends(get_db)],
):
    try:
        # 기존 인증 서비스에서 Access Token 발급
        access_token = login_user(
            session=session,
            email=request.email,
            password=request.password,
        )

        # 인증된 사용자 조회
        user = find_user_by_email(
            session,
            request.email.strip().lower(),
        )

        if user is None:
            raise InvalidCredentialsError(
                "이메일 또는 비밀번호가 올바르지 않습니다."
            )

        # Refresh Token 발급 및 DB 저장
        refresh_token = issue_refresh_token(
            session=session,
            user_id=user.id,
        )

        session.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    except InvalidCredentialsError as exc:
        session.rollback()
        raise HTTPException(
            status_code=401,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(
            status_code=503,
            detail="로그인 처리에 실패했습니다.",
        ) from exc

@router.post(
    "/browser-login",
    dependencies=[Depends(validate_browser_origin)],
)
def browser_login(
    request: UserLoginRequest,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
):
    try:
        login_user(
            session=session,
            email=request.email,
            password=request.password,
        )

        user = find_user_by_email(
            session,
            request.email.strip().lower(),
        )

        if user is None:
            raise InvalidCredentialsError(
                "이메일 또는 비밀번호가 올바르지 않습니다."
            )

        refresh_token = issue_refresh_token(
            session=session,
            user_id=user.id,
        )

        session.commit()

        set_refresh_cookie(response, refresh_token)

        return {
            "message": "브라우저 로그인 성공",
        }

    except InvalidCredentialsError as exc:
        session.rollback()
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        ) from exc

    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(
            status_code=503,
            detail="브라우저 로그인에 실패했습니다.",
        ) from exc

# 브라우저용 Refresh API
# 요청 출처를 검증하여 허용된 브라우저 요청만 처리
# 운영 환경에서는 HTTPS와 추가적인 CSRF 방어를 함께 적용
@router.post(
    "/browser-refresh",
    dependencies=[Depends(validate_browser_origin)],
)
def browser_refresh(
    response: Response,
    session: Annotated[Session, Depends(get_db)],
    refresh_token: Annotated[
        str | None,
        Cookie(alias=REFRESH_COOKIE_NAME),
    ] = None,
):
    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="인증 쿠키가 없습니다.",
        )

    try:
        user_id, new_refresh_token = rotate_refresh_token(
            session=session,
            raw_token=refresh_token,
        )

        new_access_token = create_access_token(user_id)

        session.commit()

        set_refresh_cookie(response, new_refresh_token)

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
        }

    except InvalidRefreshTokenError as exc:
        session.rollback()
        response.delete_cookie(
            key=REFRESH_COOKIE_NAME,
            path="/",
        )
        raise HTTPException(
            status_code=401,
            detail="유효하지 않은 인증 세션입니다.",
        ) from exc

    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(
            status_code=503,
            detail="브라우저 인증 갱신에 실패했습니다.",
        ) from exc

# 쿠키 기반 인증 복원 API
@router.post(
    "/browser-restore",
    dependencies=[Depends(validate_browser_origin)],
)
def browser_restore(
    database: Annotated[Session, Depends(get_db)],
    refresh_token: Annotated[
        str | None,
        Cookie(alias=REFRESH_COOKIE_NAME),
    ] = None,
):
    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="인증 쿠키가 없습니다.",
        )

    token = find_refresh_token_by_hash(
        database,
        hash_refresh_token(refresh_token),
    )

    if token is None:
        raise HTTPException(
            status_code=401,
            detail="유효하지 않은 인증 세션입니다.",
        )

    if token.revoked_at is not None:
        raise HTTPException(
            status_code=401,
            detail="폐기된 인증 세션입니다.",
        )

    if token.expires_at <= datetime.now(UTC):
        raise HTTPException(
            status_code=401,
            detail="만료된 인증 세션입니다.",
        )

    return {
        "access_token": create_access_token(token.user_id),
        "token_type": "bearer",
    }

# 브라우저 로그아웃 API
@router.post(
    "/browser-logout", 
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(validate_browser_origin)],
)
def browser_logout(
    response: Response,
    session: Annotated[Session, Depends(get_db)],
    refresh_token: Annotated[
        str | None,
        Cookie(alias=REFRESH_COOKIE_NAME),
    ] = None,
):
    try:
        if refresh_token:
            revoke_refresh_token(
                session=session,
                raw_token=refresh_token,
            )

        session.commit()

        response.delete_cookie(
            key=REFRESH_COOKIE_NAME,
            path="/",
        )

    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(
            status_code=503,
            detail="브라우저 로그아웃에 실패했습니다.",
        ) from exc

@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(
    request: TokenRefreshRequest,
    session: Annotated[Session, Depends(get_db)],
):
    try:
        # 기존 Refresh Token 검증 및 교체
        user_id, new_refresh_token = rotate_refresh_token(
            session=session,
            raw_token=request.refresh_token,
        )

        # 새로운 Access Token 발급
        new_access_token = create_access_token(user_id)

        # 기존 토큰 폐기와 신규 토큰 발급을 함께 커밋
        session.commit()

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    except InvalidRefreshTokenError as exc:
        session.rollback()
        raise HTTPException(
            status_code=401,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(
            status_code=503,
            detail="토큰 갱신 처리에 실패했습니다.",
        ) from exc

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: TokenLogoutRequest,
    session: Annotated[Session, Depends(get_db)],
):
    try:
        revoke_refresh_token(
            session=session,
            raw_token=request.refresh_token,
        )

        session.commit()

    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(
            status_code=503,
            detail="로그아웃 처리에 실패했습니다.",
        ) from exc

@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user

# HTML 폼 데이터
@router.post(
    "/browser-signin",
    dependencies=[Depends(validate_browser_origin)],
    include_in_schema=False,
)
def browser_signin(
    database: Annotated[Session, Depends(get_db)],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    csrf_token: Annotated[str | None, Form()] = None,
    csrf_cookie: Annotated[
        str | None,
        Cookie(alias=CSRF_COOKIE_NAME),
    ] = None,
):
    # 검증에 실패했을 때 HTTPException(403)이 정상적으로 반환
    validate_csrf_token(csrf_cookie, csrf_token)

    # 아래는 기존 로그인 처리 코드 그대로 유지
    try:
        # 기존 로그인 서비스로 이메일/비밀번호 검증
        login_user(
            session=database,
            email=email,
            password=password,
        )

        user = find_user_by_email(
            database,
            email.strip().lower(),
        )

        if user is None:
            raise InvalidCredentialsError(
                "이메일 또는 비밀번호가 올바르지 않습니다."
            )

        refresh_token = issue_refresh_token(
            session=database,
            user_id=user.id,
        )

        database.commit()

    except InvalidCredentialsError:
        database.rollback()
        return HTMLResponse(
            content=(
                "<h3>이메일 또는 비밀번호가 올바르지 않습니다.</h3>"
                '<a href="/api/v1/auth/browser-signin">'
                "로그인 화면으로 돌아가기</a>"
            ),
            status_code=401,
        )

    except SQLAlchemyError:
        database.rollback()
        return HTMLResponse(
            content="<h3>로그인 처리 중 오류가 발생했습니다.</h3>",
            status_code=503,
        )

    # 로그인 성공 후 Streamlit으로 이동
    streamlit_url = os.getenv(
        "STREAMLIT_APP_URL",
        "http://localhost:8501",
    )

    response = RedirectResponse(
        url=streamlit_url,
        status_code=303,
    )

    # 브라우저가 직접 받는 리다이렉트 응답에 쿠키 설정
    set_refresh_cookie(response, refresh_token)

    return response


@router.post(
    "/browser-signout",
    dependencies=[Depends(validate_browser_origin)],
    include_in_schema=False,
)
def browser_signout(
    database: Annotated[Session, Depends(get_db)],
    refresh_token: Annotated[
        str | None,
        Cookie(alias=REFRESH_COOKIE_NAME),
    ] = None,
    csrf_token: Annotated[str | None, Form()] = None,
    csrf_cookie: Annotated[
        str | None,
        Cookie(alias=CSRF_COOKIE_NAME),
    ] = None,
):
    validate_csrf_token(
        csrf_cookie,
        csrf_token,
        binding=refresh_token,
    )

    # 아래는 기존 토큰 폐기 및
    # 쿠키 삭제, 리다이렉트 코드 그대로 유지
    try:
        if refresh_token:
            revoke_refresh_token(
                database,
                raw_token=refresh_token,
            )

        database.commit()

    except SQLAlchemyError as exc:
        database.rollback()
        raise HTTPException(
            status_code=503,
            detail="로그아웃 처리에 실패했습니다.",
        ) from exc

    streamlit_url = os.getenv(
        "STREAMLIT_APP_URL",
        "http://localhost:8501",
    )

    response = RedirectResponse(
        url=streamlit_url,
        status_code=status.HTTP_303_SEE_OTHER,
    )

    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/",
    )

    return response
