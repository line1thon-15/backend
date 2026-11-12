"""보호자 리포트 A11 `GET /children/{child_id}/report` (T-25 — F-30 ①②③④).

응답 DTO는 Architecture "응답 DTO" GuardianReport 그대로. 모든 모델은 필드를 명시 나열하고 추가 필드를 금지한다
(`extra="forbid"` — "보호자용 응답 금지 필드", DECISIONS #23).
"""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict

from app.api.dependencies import require_guardian_role
from app.services.guardian_report import GuardianReportService

router = APIRouter()

AreaValue = Literal["scam", "identity_lending", "friend_pressure"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ChildRef(_Strict):
    child_id: UUID
    nickname: str


class AreaProgressView(_Strict):
    area: AreaValue
    practice_count: int
    last_practiced_at: datetime | None


class WeakCueView(_Strict):
    cue_id: str
    label: str


class NoticeView(_Strict):
    notice_id: UUID
    kind: Literal["safety", "trusted_contact"]
    occurred_at: datetime
    level: Literal["red", "yellow"] | None
    area: AreaValue | None
    channel: Literal["call", "sms"] | None


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


class SummaryItem(_Strict):
    area: AreaValue | None
    sentences: list[str]


class GuardianSummaryView(_Strict):
    status: Literal["ok", "insufficient", "unavailable"]
    unit: Literal["overall", "area"]
    items: list[SummaryItem]


class GuardianReportResponse(_Strict):
    child: ChildRef
    areas: list[AreaProgressView]
    weak_cues: list[WeakCueView]
    notices: list[NoticeView]
    metrics: list[MetricView]
    summary: GuardianSummaryView


@router.get("/children/{child_id}/report", response_model=GuardianReportResponse)
def get_guardian_report(
    child_id: UUID,
    request: Request,
    guardian_id: UUID = Depends(require_guardian_role),
) -> GuardianReportResponse:
    service: GuardianReportService = request.app.state.guardian_report_service
    report = service.get_report(guardian_id=guardian_id, child_id=child_id)
    return GuardianReportResponse(
        child=ChildRef(child_id=report.child.child_id, nickname=report.child.nickname),
        areas=[
            AreaProgressView(
                area=area.area,
                practice_count=area.practice_count,
                last_practiced_at=area.last_practiced_at,
            )
            for area in report.areas
        ],
        weak_cues=[WeakCueView(cue_id=cue.cue_id, label=cue.label) for cue in report.weak_cues],
        notices=[
            NoticeView(
                notice_id=notice.notice_id,
                kind=notice.kind,
                occurred_at=notice.occurred_at,
                level=notice.level,
                area=notice.area,
                channel=notice.channel,
            )
            for notice in report.notices
        ],
        # 성장 지표 — T-46 병합(T-90) 때 연결, 그 전에는 빈 목록
        metrics=[],
        summary=GuardianSummaryView(
            status=report.summary.status,
            unit=report.summary.unit,
            items=[],
        ),
    )
