# 요청·응답 스키마
# 사용자 ID는 클라이언트가 전달하는 게 아니라 JWT에서 확인한 로그인 사용자 정보로 설정
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatCreateRequest(BaseModel):
    title: str = Field(default="새 대화", min_length=1, max_length=200)


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    created_at: datetime

class ChatListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[ChatResponse]

from pydantic import field_validator


class ChatMessageCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=20000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("메시지 내용은 비워둘 수 없습니다.")

        return value


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime