"""아이용 성장(A19)·홈(A13) 응답 조립 (T-90 — F-28, F-29, N-12).

근거: Architecture A13·A19 행, GrowthView·BadgeView·MetricView·CueCard DTO, "성장 계산 규칙" 절,
DECISIONS #88(`level` null)·#122·#124(조립 담당 T-90).

조립만 한다 — 새 계산 규칙을 넣지 않는다(N-12).
- 배지·연속 기록: T-45 `BadgeService.badges_and_streak`
- 지표 3개·더 연습이 필요한 단서: T-46 `GrowthMetricsService`
- 영역별 진행 수: 보호자 리포트(T-25)와 같은 domain 함수 `area_progress`(종료 세션 수)
- 단서 카드 문구: 콘텐츠 `clues.json` name·description(연습 결과 T-16과 같은 원천)
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.domain.guardian_report import EndedSession, area_progress
from app.domain.metrics import METRIC_LABELS, MetricResult
from app.services.badges import Badge, BadgeRepository, BadgeService
from app.services.growth import GrowthMetricsService


@dataclass(frozen=True)
class TrustedContact:
    name: str
    phone: str


class TrustedContactRepository(Protocol):
    def trusted_contact(self, child_id: UUID) -> TrustedContact | None: ...


@dataclass(frozen=True)
class CueCard:
    cue_id: str
    label: str
    sentence: str


@dataclass(frozen=True)
class GrowthArea:
    area: str
    practice_count: int
    badges: tuple[Badge, ...]


@dataclass(frozen=True)
class LabeledMetric:
    label: str
    result: MetricResult


@dataclass(frozen=True)
class GrowthOutput:
    areas: tuple[GrowthArea, ...]
    streak_days: int
    needs_practice_cues: tuple[CueCard, ...]
    metrics: tuple[LabeledMetric, ...]


@dataclass(frozen=True)
class HomeOutput:
    areas: tuple[str, ...]
    badges: tuple[Badge, ...]
    streak_days: int
    trusted_contact: TrustedContact | None


class ChildViewsService:
    def __init__(
        self,
        *,
        badge_service: BadgeService,
        metrics_service: GrowthMetricsService,
        sessions: BadgeRepository,
        contacts: TrustedContactRepository,
        areas: Sequence[str],
        cue_cards: Mapping[str, tuple[str, str]],
        metric_labels: Mapping[str, str] = METRIC_LABELS,
    ) -> None:
        self._badge_service = badge_service
        self._metrics_service = metrics_service
        self._sessions = sessions
        self._contacts = contacts
        self._areas = tuple(areas)
        self._cue_cards = cue_cards
        self._metric_labels = metric_labels

    def growth(self, child_id: UUID) -> GrowthOutput:
        badge_streak = self._badge_service.badges_and_streak(child_id)
        progress = area_progress(
            self._areas,
            (EndedSession(area=s.area, ended_at=s.ended_at) for s in self._sessions.ended_sessions(child_id)),
        )
        return GrowthOutput(
            areas=tuple(
                GrowthArea(
                    area=item.area,
                    practice_count=item.practice_count,
                    badges=tuple(b for b in badge_streak.badges if b.area == item.area),
                )
                for item in progress
            ),
            streak_days=badge_streak.streak_days,
            # 콘텐츠에 없는 단서 ID는 싣지 않는다 — 보호자 약점 단서(T-25 GuardianReportService)와 같은 처리
            needs_practice_cues=tuple(
                self._cue_card(cue_id)
                for cue_id in self._metrics_service.needs_practice_cue_ids(child_id)
                if cue_id in self._cue_cards
            ),
            metrics=tuple(
                LabeledMetric(label=self._metric_labels[m.metric_id], result=m)
                for m in self._metrics_service.metrics(child_id)
            ),
        )

    def home(self, child_id: UUID) -> HomeOutput:
        badge_streak = self._badge_service.badges_and_streak(child_id)
        return HomeOutput(
            areas=self._areas,
            badges=badge_streak.badges,
            streak_days=badge_streak.streak_days,
            trusted_contact=self._contacts.trusted_contact(child_id),
        )

    def _cue_card(self, cue_id: str) -> CueCard:
        label, sentence = self._cue_cards[cue_id]
        return CueCard(cue_id=cue_id, label=label, sentence=sentence)
