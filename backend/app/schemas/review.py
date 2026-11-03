from datetime import datetime

from pydantic import BaseModel, Field


# AnalyzeRequest는 클라이언트가 전송하는 데이터의 형태를 정의
# max_length=100_000으로 지나치게 큰 코드 입력을 제한하고, 
# 공백만 입력한 경우는 기존 서비스 계층에서 검사
class AnalyzeRequest(BaseModel):
    code: str = Field(min_length=1, max_length=100_000)


class AnalyzeIssue(BaseModel):
    line: int
    column: int
    code: str
    message: str


# AnalyzeResponse는 서버가 반환하는 데이터의 형태를 정의
class AnalyzeResponse(BaseModel):
    total: int
    issues: list[AnalyzeIssue]

# 요청 모델은 기존 AnalyzeRequest를 재사용
class AIReviewResponse(BaseModel):
    review: str

class ReviewDetailResponse(BaseModel):
    id: int
    source_code: str
    analysis_type: str
    result: str
    created_at: datetime

class ReviewListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[ReviewDetailResponse]

# 통계 응답
class ReviewStatsResponse(BaseModel):
    total: int
    ruff_count: int
    ai_count: int