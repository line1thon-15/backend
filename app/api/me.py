"""아이용 홈 A13 `GET /me/home`·성장 A19 `GET /me/growth` (T-90 — F-28, F-29).

응답 DTO는 Architecture "API 규격" A13 행·"응답 DTO" GrowthView·BadgeView·MetricView·CueCard 그대로.
모든 모델은 필드를 명시 나열하고 추가 필드를 금지한다(`extra="forbid"`).
인가: 아이 세션만 — 미로그인 401 `UNAUTHENTICATED`, 보호자 세션 403 `FORBIDDEN_ROLE`(Architecture "역할 분리").
대상 아이는 세션에서만 정한다(경로·쿼리에 아이 ID 없음 — 다른 아이 기록에 접근할 입력이 없다).
"""

from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict

from app.api.dependencies import require_child_role
from app.services.badges import Badge
from app.services.child_views import ChildViewsService

router = APIRouter()

AreaValue = Literal["scam", "identity_lending", "friend_pressure"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BadgeView(_Strict):
    badge_id: str
    area: AreaValue | None
    label: str


class CueCardView(_Strict):
    cue_id: str
    label: str
    sentence: str


class TrendPoint(_Strict):
    date: date
    value: float


class MetricView(_Strict):
    metric_id: Literal["missed_ratio", "first_seen_accuracy", "ahead_of_ai_ratio"]
    label: str
    status: Literal["ok", "insufficient"]
    level: Literal["red", "yellow", "green"] | None
    current: float | None
    previous: float | None
    trend: list[TrendPoint]


class GrowthAreaView(_Strict):
    area: AreaValue
    practice_count: int
    badges: list[BadgeView]


class GrowthResponse(_Strict):
    areas: list[GrowthAreaView]
    streak_days: int
    needs_practice_cues: list[CueCardView]
    metrics: list[MetricView]


class HomeAreaView(_Strict):
    area: AreaValue


class TrustedContactView(_Strict):
    name: str
    phone: str


class HomeResponse(_Strict):
    areas: list[HomeAreaView]
    badges: list[BadgeView]
    streak_days: int
    trusted_contact: TrustedContactView | None


def _badge_view(badge: Badge) -> BadgeView:
    return BadgeView(badge_id=badge.badge_id, area=badge.area, label=badge.label)


@router.get("/me/growth", response_model=GrowthResponse)
def get_my_growth(
    request: Request,
    child_id: UUID = Depends(require_child_role),
) -> GrowthResponse:
    service: ChildViewsService = request.app.state.child_views_service
    output = service.growth(child_id)
    return GrowthResponse(
        areas=[
            GrowthAreaView(
                area=item.area,
                practice_count=item.practice_count,
                badges=[_badge_view(badge) for badge in item.badges],
            )
            for item in output.areas
        ],
        streak_days=output.streak_days,
        needs_practice_cues=[
            CueCardView(cue_id=card.cue_id, label=card.label, sentence=card.sentence)
            for card in output.needs_practice_cues
        ],
        metrics=[
            MetricView(
                metric_id=metric.result.metric_id,
                label=metric.label,
                status=metric.result.status,
                level=metric.result.level,
                current=metric.result.current,
                previous=metric.result.previous,
                trend=[TrendPoint(date=point.date, value=point.value) for point in metric.result.trend],
            )
            for metric in output.metrics
        ],
    )


@router.get("/me/home", response_model=HomeResponse)
def get_my_home(
    request: Request,
    child_id: UUID = Depends(require_child_role),
) -> HomeResponse:
    service: ChildViewsService = request.app.state.child_views_service
    output = service.home(child_id)
    contact = output.trusted_contact
    return HomeResponse(
        areas=[HomeAreaView(area=area) for area in output.areas],
        badges=[_badge_view(badge) for badge in output.badges],
        streak_days=output.streak_days,
        trusted_contact=None if contact is None else TrustedContactView(name=contact.name, phone=contact.phone),
    )
