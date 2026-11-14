"""보호자 학습 요약 입력 조립·응답 검증 (T-76 — F-47 ②③⑥). 표준 라이브러리만 쓰는 순수 함수.

근거: Architecture.md:363 `POST /internal/v1/summary` 행 — 이번 기간(#88 창)에 종료 세션이 있는 영역마다 1회,
요청 `{area, practice_count, found_clues, missed_clues, growth_level: null}`, 검증 S1~S3. DECISIONS #103·#114.

- 입력은 `status = ended` 세션만, 기간 거르기는 리포지토리 몫이다(멈춘 연습 제외 — F-11 ⑧).
- 단서는 ID로만 다룬다. 이름으로 바꾸는 것은 서비스가 콘텐츠로 한다(대화 문장·선택지·감정 값 없음 — F-47 ③).
"""

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

# 기록 부족 기준 — Architecture A-18 [가정] 기본값 1 (PRD OQ 58 미결, 답에 따라 이 값만 교체)
SUMMARY_MIN_ENDED_SESSIONS = 1
# S3 길이 상한(설정 상수) — 값은 설계에 없음. AI 쪽 app/summary.py MAX_CHARS = 200과 같게 둠
# (2026-11-14 메인 세션에 확인 요청 중 — 답에 따라 이 값만 교체)
SUMMARY_MAX_CHARS = 200

_NUMBER = re.compile(r"\d+")


@dataclass(frozen=True)
class SummarySession:
    """이번 기간 종료 세션 1개 — 영역과 단서 판정 ID만."""

    area: str
    found: tuple[str, ...]
    missed: tuple[str, ...]


@dataclass(frozen=True)
class AreaSummaryInput:
    area: str
    practice_count: int
    found_cue_ids: tuple[str, ...]
    missed_cue_ids: tuple[str, ...]


def summary_inputs(
    sessions: Iterable[SummarySession],
    areas: Sequence[str],
    cue_order: Sequence[str],
) -> tuple[AreaSummaryInput, ...] | None:
    """영역마다 요약 입력. 결과 순서 = `areas` 순서, 기록 없는 영역은 빠진다.

    종료 세션 수가 `SUMMARY_MIN_ENDED_SESSIONS` 미만이면 None(기록 부족 — AI 미호출).
    단서 목록은 중복 제거, 순서 = `cue_order`(콘텐츠 순서). `cue_order`에 없는 단서는 이름을 보일 수 없어 뺀다.
    한 기간에 찾기도·놓치기도 한 단서는 두 목록에 모두 들어간다(DECISIONS #103 문구 그대로).
    """
    counts: dict[str, int] = {}
    found: dict[str, set[str]] = {}
    missed: dict[str, set[str]] = {}
    total = 0
    for session in sessions:
        if session.area not in areas:
            raise ValueError(f"unknown area: {session.area!r}")
        total += 1
        counts[session.area] = counts.get(session.area, 0) + 1
        found.setdefault(session.area, set()).update(session.found)
        missed.setdefault(session.area, set()).update(session.missed)
    if total < SUMMARY_MIN_ENDED_SESSIONS:
        return None
    return tuple(
        AreaSummaryInput(
            area=area,
            practice_count=counts[area],
            found_cue_ids=tuple(cue for cue in cue_order if cue in found[area]),
            missed_cue_ids=tuple(cue for cue in cue_order if cue in missed[area]),
        )
        for area in areas
        if area in counts
    )


def accept_summary(text: str | None, input_values: Iterable[str]) -> bool:
    """AI 요약 문장 검증 — S1 null·공백만 아님 / S2 숫자는 입력 값에 있는 것만(#53) / S3 길이 상한."""
    if text is None or not text.strip():
        return False
    allowed = set(_NUMBER.findall(" ".join(input_values)))
    if not set(_NUMBER.findall(text)) <= allowed:
        return False
    return len(text) <= SUMMARY_MAX_CHARS
