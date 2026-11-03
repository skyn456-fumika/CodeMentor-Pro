# 대화 세션 생성 API
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_user
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.schemas.chat import ChatCreateRequest, ChatResponse
from backend.app.services.chat_service import create_chat_session

router = APIRouter(prefix="/chats", tags=["Chats"])


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_chat(
    request: ChatCreateRequest,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        return create_chat_session(
            session=session,
            user_id=current_user.id,
            title=request.title,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="대화 세션 생성에 실패했습니다.",
        ) from exc

from fastapi import Query

from backend.app.schemas.chat import ChatListResponse
from backend.app.services.chat_service import (
    get_chat_session,
    get_chat_sessions,
)


# 대화방 목록 조회
@router.get("", response_model=ChatListResponse)
def get_chat_list(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
):
    try:
        chats, total = get_chat_sessions(
            session=session,
            user_id=current_user.id,
            page=page,
            size=size,
        )

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="대화 목록 조회에 실패했습니다.",
        ) from exc

    return ChatListResponse(
        total=total,
        page=page,
        size=size,
        items=[
            ChatResponse.model_validate(chat)
            for chat in chats
        ],
    )

# 내 대화방 상세 조회
@router.get("/{chat_id}", response_model=ChatResponse)
def get_chat_detail(
    chat_id: int,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if chat_id < 1:
        raise HTTPException(
            status_code=422,
            detail="올바른 대화 세션 ID를 입력해 주세요.",
        )

    try:
        chat = get_chat_session(
            session=session,
            chat_id=chat_id,
            user_id=current_user.id,
        )

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="대화 세션 조회에 실패했습니다.",
        ) from exc

    if chat is None:
        raise HTTPException(
            status_code=404,
            detail="대화 세션을 찾을 수 없습니다.",
        )

    return chat

# 대화 메시지 저장 API
from backend.app.schemas.chat import (
    ChatMessageCreateRequest,
    ChatMessageResponse,
)
from backend.app.services.chat_message_service import (
    ChatNotFoundError,
    create_user_message,
    get_chat_messages,
)


# 사용자 메시지 저장
@router.post(
    "/{chat_id}/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_message(
    chat_id: int,
    request: ChatMessageCreateRequest,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        return create_user_message(
            session=session,
            chat_id=chat_id,
            user_id=current_user.id,
            content=request.content,
        )

    except ChatNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="메시지 저장에 실패했습니다.",
        ) from exc

# 대화방의 메시지 목록 조회
@router.get(
    "/{chat_id}/messages",
    response_model=list[ChatMessageResponse],
)
def get_messages(
    chat_id: int,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        return get_chat_messages(
            session=session,
            chat_id=chat_id,
            user_id=current_user.id,
        )

    except ChatNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="메시지 조회에 실패했습니다.",
        ) from exc

from backend.app.services.ai_service import AIServiceError
from backend.app.services.chat_message_service import ask_chat


# AI 질문 API
@router.post(
    "/{chat_id}/ask",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def ask_ai(
    chat_id: int,
    request: ChatMessageCreateRequest,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        return ask_chat(
            session=session,
            chat_id=chat_id,
            user_id=current_user.id,
            question=request.content,
        )

    except ChatNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except AIServiceError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="AI 대화 저장에 실패했습니다.",
        ) from exc