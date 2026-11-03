from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse

from backend.app.core.browser_csrf import (
    CSRF_COOKIE_NAME,
    create_csrf_token,
)
from backend.app.core.cookie_settings import COOKIE_SECURE

router = APIRouter()

# FastAPI 브라우저 로그인 화면 구현
@router.get("/browser-signin", response_class=HTMLResponse)
def browser_signin_page(response: Response):
    csrf_token = create_csrf_token()

    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        path="/",
        max_age=600,
    )

    html = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">
        <title>CodeMentor Pro - 로그인</title>
        <style>
            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #f3f5f9;
                font-family: Arial, sans-serif;
            }

            .login-box {
                width: 100%;
                max-width: 400px;
                padding: 36px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
            }

            h1 {
                margin: 0 0 8px;
                text-align: center;
            }

            .description {
                margin-bottom: 28px;
                color: #666;
                text-align: center;
                font-size: 14px;
            }

            label {
                display: block;
                margin: 16px 0 6px;
                font-weight: bold;
                font-size: 14px;
            }

            input {
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 15px;
            }

            button {
                width: 100%;
                margin-top: 24px;
                padding: 13px;
                border: none;
                border-radius: 8px;
                background: #2563eb;
                color: white;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
            }

            button:hover {
                background: #1d4ed8;
            }
        </style>
    </head>
    <body>
        <main class="login-box">
            <h1>💻 CodeMentor Pro</h1>
            <p class="description">
                AI 코드 분석 서비스 로그인
            </p>

            <form method="post"
                  action="/api/v1/auth/browser-signin">

                <input
                    type="hidden"
                    name="csrf_token"
                    value="__CSRF_TOKEN__"
                >

                <label for="email">이메일</label>
                <input
                    id="email"
                    type="email"
                    name="email"
                    autocomplete="username"
                    required
                >

                <label for="password">비밀번호</label>
                <input
                    id="password"
                    type="password"
                    name="password"
                    autocomplete="current-password"
                    required
                >

                <button type="submit">로그인</button>
            </form>
        </main>
    </body>
    </html>
    """

    return html.replace("__CSRF_TOKEN__", csrf_token)

# 로그아웃 확인 화면
@router.get("/browser-signout", response_class=HTMLResponse)
def browser_signout_page(response: Response):
    csrf_token = create_csrf_token()

    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        path="/",
        max_age=600,
    )

    html = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">
        <title>CodeMentor Pro - 로그아웃</title>
        <style>
            body {
                margin: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #f3f5f9;
                font-family: Arial, sans-serif;
            }

            .logout-box {
                width: 360px;
                max-width: 90%;
                padding: 36px;
                border-radius: 16px;
                background: white;
                text-align: center;
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
            }

            p {
                color: #666;
                line-height: 1.6;
            }

            button, a {
                display: block;
                box-sizing: border-box;
                width: 100%;
                padding: 13px;
                margin-top: 12px;
                border-radius: 8px;
                font-size: 15px;
                text-decoration: none;
                cursor: pointer;
            }

            button {
                color: white;
                border: none;
                background: #dc2626;
            }

            a {
                color: #333;
                background: #e5e7eb;
            }
        </style>
    </head>
    <body>
        <main class="logout-box">
            <h2>💻 CodeMentor Pro</h2>
            <p>정말 로그아웃하시겠습니까?</p>

            <form method="post"
                  action="/api/v1/auth/browser-signout">

                <input
                    type="hidden"
                    name="csrf_token"
                    value="__CSRF_TOKEN__"
                >

                <button type="submit">
                    로그아웃
                </button>
            </form>

            <a href="http://localhost:8501">
                취소하고 돌아가기
            </a>
        </main>
    </body>
    </html>
    """

    return html.replace("__CSRF_TOKEN__", csrf_token)