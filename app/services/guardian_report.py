"""보호자 리포트 A11 (T-25 — F-30 ①②③④, N-05).

- 인가: `get_owned_child(guardian_id, child_id)` 한 쿼리 — 없거나 남의 아이면 404 `CHILD_NOT_FOUND`.
- 원천: practice_sessions·cue_results(`status = ended`만). practice_turns는 읽지 않는다.
- `notices`·`metrics`·`summary`는 이 브랜치에 원천이 없다(guardian_notices 테이블 없음, 지표 T-46, 요약 T-76).
  빈 목록·자리표시 요약으로 채운다 — T-25 보고 Open Question(확정 동작 아님).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from uuid import UUID

from app.core.errors import AppError
from app.domain.guardian_report import AreaProgress, area_progress, weak_cues
from app.services.ports import GuardianReportRepository, ReportChild


@dataclass(frozen=True)
class WeakCueLabel:
    cue_id: str
    label: str


@dataclass(frozen=True)
class GuardianSummary:
    status: str  # ok | insufficient | unavailable
    unit: str  # overall | area — 1차는 area (DECISIONS #114)
    items: tuple = ()


# 요약 생성(T-76) 전 자리표시 — 1차 단위 "area"(#114), 생성하지 않았으므로 items 없음.
PENDING_SUMMARY = GuardianSummary(status="unavailable", unit="area")


@dataclass(frozen=True)
class GuardianReportData:
    child: ReportChild
    areas: list[AreaProgress]
    weak_cues: list[WeakCueLabel]
    notices: tuple = ()
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
            WeakCueLabel(cue_id=cue.cue_id, label=self._clue_labels[cue.cue_id])
            for cue in weak_cues(self._repository.ended_cue_outcomes(child.child_id))
            if cue.cue_id in self._clue_labels
        ]
        return GuardianReportData(child=child, areas=areas, weak_cues=labeled)
