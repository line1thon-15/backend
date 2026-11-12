"""보호자 리포트 A11 (T-25 — F-30 ①②③④, N-05).

- 인가: `get_owned_child(guardian_id, child_id)` 한 쿼리 — 없거나 남의 아이면 404 `CHILD_NOT_FOUND`.
- 원천: practice_sessions·cue_results(`status = ended`만). practice_turns는 읽지 않는다.
- `notices`: guardian_notices(2026-11-12 사용자 답 "T-25에 포함 (추천)"). 최신 순.
- `metrics`: T-46 병합 전이라 빈 목록. `summary`: DECISIONS #123 고정 임시값 `insufficient`, AI 미호출.
- 약점 단서: 공통 함수 `select_weak_cues`(DECISIONS #122).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from uuid import UUID

from app.core.errors import AppError
from app.domain.guardian_report import AreaProgress, area_progress
from app.domain.weak_cues import select_weak_cues
from app.services.ports import GuardianNoticeRecord, GuardianReportRepository, ReportChild


@dataclass(frozen=True)
class WeakCueLabel:
    cue_id: str
    label: str


@dataclass(frozen=True)
class GuardianSummary:
    status: str  # ok | insufficient | unavailable
    unit: str  # overall | area — 1차는 area (DECISIONS #114)
    items: tuple = ()


# 요약 생성(T-76) 전 임시값 — DECISIONS #123, 2026-11-12 사용자 답 "아직 기록이 적어요 (추천)"(설명 원문 "status=insufficient.
# 오류처럼 보이지 않고 자연스러워요. T-76이 끝나면 실제 요약으로 바뀌어요."). 1차 단위 "area"(#114), items 없음.
PENDING_SUMMARY = GuardianSummary(status="insufficient", unit="area")


@dataclass(frozen=True)
class GuardianReportData:
    child: ReportChild
    areas: list[AreaProgress]
    weak_cues: list[WeakCueLabel]
    notices: tuple[GuardianNoticeRecord, ...] = ()
    metrics: tuple = ()
    summary: GuardianSummary = field(default=PENDING_SUMMARY)


class GuardianReportService:
    def __init__(
        self,
        repository: GuardianReportRepository,
        area_ids: Sequence[str],
        clue_labels: Mapping[str, str],
    ) -> None:
        self._repository = repository
        self._area_ids = tuple(area_ids)
        self._clue_labels = clue_labels

    def get_report(self, guardian_id: UUID, child_id: UUID) -> GuardianReportData:
        child = self._repository.get_owned_child(guardian_id, child_id)
        if child is None:
            raise AppError(code="CHILD_NOT_FOUND", status_code=404, message="child not found")

        areas = area_progress(self._area_ids, self._repository.ended_sessions(child.child_id))
        # 콘텐츠에 없는 단서(콘텐츠 교체 등)는 이름을 보일 수 없어 뺀다 — 원문·ID 추측 표시 없음
        labeled = [
            WeakCueLabel(cue_id=cue_id, label=self._clue_labels[cue_id])
            for cue_id in select_weak_cues(self._repository.ended_cue_outcomes(child.child_id))
            if cue_id in self._clue_labels
        ]
        return GuardianReportData(
            child=child,
            areas=areas,
            weak_cues=labeled,
            notices=tuple(self._repository.notices(child.child_id)),
        )
