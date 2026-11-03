import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.schemas.review import (
    AIReviewResponse,
    AnalyzeRequest,
    AnalyzeResponse,
)
from backend.app.services.ai_service import (
    AIServiceError,
    review_code,
)
from backend.app.services.analyzer_service import (
    AnalyzerError,
    analyze_code,
)
from backend.app.services.review_service import create_review

logger = logging.getLogger(__name__)

from backend.app.schemas.review import ReviewDetailResponse
from backend.app.services.review_service import get_review

router = APIRouter(prefix="/reviews", tags=["Reviews"])

# 분석 Router에 JWT 인증 적용
from typing import Annotated

from fastapi import Query

from backend.app.core.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas.review import ReviewListResponse, ReviewStatsResponse
from backend.app.services.review_service import get_reviews, get_user_review_stats


# 정상 분석 완료 (문제 발견 포함) - 200(OK)
# 잘못된 코드 입력 - 422(Unprocessable Entity)
# Ruff 분석 서비스 실행 실패 - 503(Service Unavailable)
@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    request: AnalyzeRequest,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        issues = analyze_code(request.code)

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except AnalyzerError as exc:
        raise HTTPException(
            status_code=503,
            detail="코드 분석 서비스를 사용할 수 없습니다.",
        ) from exc

    # Ruff 분석이 정상적으로 완료된 경우에만 DB에 저장한다는 것
    try:
        create_review(
            session=session,
            source_code=request.code,
            analysis_type="RUFF",
            result=json.dumps(issues, ensure_ascii=False),
            user_id=current_user.id,
        )

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="분석 기록 저장에 실패했습니다.",
        ) from exc

    return AnalyzeResponse(
        total=len(issues),
        issues=issues,
    )

# Gemini 응답을 받은 뒤 DB에 기록을 저장한다는 것
@router.post("/ai", response_model=AIReviewResponse)
def ai_review(
    request: AnalyzeRequest,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        result = review_code(request.code)

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except AIServiceError as exc:
        logger.exception("Gemini AI 리뷰 실패")
        raise HTTPException(
            status_code=503,
            detail="AI 리뷰 서비스를 사용할 수 없습니다.",
        ) from exc

    try:
        create_review(
            session=session,
            source_code=request.code,
            analysis_type="AI",
            result=result,
            user_id=current_user.id,
        )

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="분석 기록 저장에 실패했습니다.",
        ) from exc

    return AIReviewResponse(review=result)

# 통계 API
@router.get("/stats", response_model=ReviewStatsResponse)
def get_my_review_stats(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return get_user_review_stats(
        session=session,
        user_id=current_user.id,
    )

# 조회 API
@router.get(
    "/{review_id}",
    response_model=ReviewDetailResponse,
)
def get_review_detail(
    review_id: int,
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if review_id < 1:
        raise HTTPException(
            status_code=422,
            detail="올바른 분석 기록 ID를 입력해 주세요.",
        )

    try:
        review = get_review(
            session=session,
            review_id=review_id,
            user_id=current_user.id,
        )

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="분석 기록 조회에 실패했습니다.",
        ) from exc

    if review is None:
        raise HTTPException(
            status_code=404,
            detail="분석 기록을 찾을 수 없습니다.",
        )

    return ReviewDetailResponse(
        id=review.id,
        source_code=review.source_code,
        analysis_type=review.analysis_type,
        result=review.result,
        created_at=review.created_at,
    )

# 목록 조회 API
@router.get("", response_model=ReviewListResponse)
def get_review_list(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
):
    try:
        reviews, total = get_reviews(
            session=session,
            page=page,
            size=size,
            user_id=current_user.id,
        )

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="분석 기록 목록 조회에 실패했습니다.",
        ) from exc

    return ReviewListResponse(
        total=total,
        page=page,
        size=size,
        items=[
            ReviewDetailResponse.model_validate(
                {
                    "id": review.id,
                    "source_code": review.source_code,
                    "analysis_type": review.analysis_type,
                    "result": review.result,
                    "created_at": review.created_at,
                }
            )
            for review in reviews
        ],
    )