"""시연 예시 기록 계획 — 순수 함수 (T-67, N-11, F-28 ②③, F-29 ④⑤⑥, F-41 ②④, F-47 ⑤).

- 날짜는 `now`(적재 시점) 기준 상대값이다 — 고정 날짜는 시연일의 7일 창을 벗어날 수 있다(Tasks T-67).
- 콘텐츠 ID(시나리오·단서·영역)는 AI 콘텐츠 사본(T-87)의 실제 값만 쓴다. 없으면 지어내지 않고 실패한다.
- 기록 행은 DECISIONS #98 형태(`choices[{id,text,kind}]`·`target_clue_id`·`revealed_clue_ids`·`ai_status`),
  `cue_results`는 `found`·`missed`만(DECISIONS #109).

계획한 값(오늘 = D0, 한국 시간 날짜. 기대 계산은 tests/integration/test_demo_seed.py 머리말):
  직전 기간(D7~D13) 4세션 — 놓친 단서가 많고 첫 답에서 의심한 세션이 적다
  이번 기간(D0~D6) 4세션 — 놓친 단서가 줄고, 놓침 0·찾음 ≥1 세션 3개(배지), D0·D1·D2 연속
  keep_secret은 두 번 놓치고 최근에도 놓침(더 연습이 필요한 단서)
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from app.content.loader import ContentBundle
from app.domain.service_time import SERVICE_TZ, service_date

# (며칠 전, 시나리오 ID, 단서 판정, 첫 답 kind) — 시간 순
_SESSION_SCHEDULE: tuple[tuple[int, str, tuple[tuple[str, str], ...], str], ...] = (
    (12, "scam_dm_parttime_01", (("too_good_pay", "missed"), ("advance_payment", "missed"), ("urgency", "found")), "doubtful"),
    (10, "scam_jobboard_link_01", (("suspicious_link", "missed"), ("personal_info", "found")), "other"),
    (9, "scam_dm_parttime_01", (("too_good_pay", "found"), ("advance_payment", "missed"), ("keep_secret", "missed")), "doubtful"),
    (8, "scam_jobboard_link_01", (("suspicious_link", "missed"), ("urgency", "found")), "correct"),
    (4, "scam_dm_parttime_01", (("too_good_pay", "found"), ("advance_payment", "found"), ("urgency", "found")), "correct"),
    (2, "scam_jobboard_link_01", (("suspicious_link", "found"), ("personal_info", "found"), ("keep_secret", "missed")), "correct"),
    (1, "scam_dm_parttime_01", (("too_good_pay", "found"), ("advance_payment", "found")), "correct"),
    (0, "scam_jobboard_link_01", (("suspicious_link", "found"), ("personal_info", "found"), ("urgency", "found")), "doubtful"),
)

# (며칠 전, 위험도, 영역) — 안전 알림 항목은 발생 시각·위험도·영역만(F-41 ④⑤)
_NOTICE_SCHEDULE: tuple[tuple[int, str, str], ...] = (
    (9, "red", "scam"),
    (2, "yellow", "scam"),
)

_SESSION_HOUR = 10  # 지난 날의 종료 시각(한국 시간 10:00)
_NOTICE_MINUTE = 30  # 지난 날의 알림 시각(한국 시간 10:30)
_TODAY_OFFSET = timedelta(minutes=30)  # 오늘 세션은 적재 30분 전 종료(자정 직후면 오늘 0시)
_SESSION_LENGTH = timedelta(minutes=5)

# 시연용 예시 문장(N-11) — 실제 대화가 아님을 드러내는 고정 문구
_DEMO_LINE = "시연용 예시 기록이에요."
_DEMO_CHOICES = (
    {"id": "c1", "text": "이상해요. 믿을 수 있는 사람에게 물어볼래요.", "kind": "correct"},
    {"id": "c2", "text": "조금 이상하지만 일단 해 볼까요?", "kind": "doubtful"},
    {"id": "c3", "text": "좋아요! 바로 할게요.", "kind": "other"},
)
_DEMO_ROLE = {"name": "시연 예시", "persona": "시연용 예시 인물", "tone": "예시 말투"}


@dataclass(frozen=True)
class DemoSession:
    area: str
    scenario_id: str
    mode: str
    is_normal: bool
    draw_index: int
    target_cue_ids: tuple[str, ...]
    cue_outcomes: tuple[tuple[str, str], ...]
    first_choice_kind: str
    started_at: datetime
    ended_at: datetime
    scenario_title: str
    child_setup: str
    ai_role_name: str
    variant: dict
    ai_line: str
    turn_choices: tuple[dict, ...]
    chosen_choice_id: str
    target_clue_id: str
    revealed_clue_ids: tuple[str, ...]


@dataclass(frozen=True)
class DemoNotice:
    level: str
    area: str
    occurred_at: datetime


@dataclass(frozen=True)
class DemoPlan:
    sessions: tuple[DemoSession, ...]
    notices: tuple[DemoNotice, ...]


def _day_start(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=SERVICE_TZ).astimezone(timezone.utc)


def _past_moment(today: date, days_ago: int, minute: int) -> datetime:
    return _day_start(today - timedelta(days=days_ago)) + timedelta(hours=_SESSION_HOUR, minutes=minute)


def _session_end(now: datetime, today: date, days_ago: int) -> datetime:
    if days_ago == 0:
        return max(_day_start(today), now - _TODAY_OFFSET)
    return _past_moment(today, days_ago, 0)


def _variant(content: ContentBundle, scenario_id: str) -> dict:
    scenario = content.scenarios[scenario_id].scenario
    return {
        "base_scenario_id": scenario.id,
        "platform": scenario.platform,
        "tone": scenario.variation_axes.tone[0],
        "context": scenario.variation_axes.context[0],
        "title": scenario.title,
        "child_setup": _DEMO_LINE,
        "opening_line": _DEMO_LINE,
        "ai_role": dict(_DEMO_ROLE),
        "clues": [clue.model_dump(mode="json") for clue in scenario.clues],
    }


def build_demo_plan(now: datetime, content: ContentBundle) -> DemoPlan:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("timezone-aware datetime required")
    now = now.astimezone(timezone.utc)
    today = service_date(now)

    sessions: list[DemoSession] = []
    for draw_index, (days_ago, scenario_id, outcomes, first_kind) in enumerate(_SESSION_SCHEDULE):
        entry = content.scenarios.get(scenario_id)
        if entry is None:
            raise ValueError(f"demo scenario not in content: {scenario_id}")
        clue_ids = tuple(clue.id for clue in entry.scenario.clues)
        unknown = [cue_id for cue_id, _ in outcomes if cue_id not in clue_ids or cue_id not in content.clues]
        if unknown:
            raise ValueError(f"demo cue not in scenario {scenario_id}: {unknown}")
        opening = tuple(clue.id for clue in entry.scenario.clues if clue.at_opening) or clue_ids[:1]
        chosen = next(choice["id"] for choice in _DEMO_CHOICES if choice["kind"] == first_kind)
        ended_at = _session_end(now, today, days_ago)
        sessions.append(
            DemoSession(
                area=entry.area,
                scenario_id=scenario_id,
                mode="area",
                is_normal=False,
                draw_index=draw_index,
                target_cue_ids=clue_ids,
                cue_outcomes=outcomes,
                first_choice_kind=first_kind,
                started_at=ended_at - _SESSION_LENGTH,
                ended_at=ended_at,
                scenario_title=entry.scenario.title,
                child_setup=_DEMO_LINE,
                ai_role_name=_DEMO_ROLE["name"],
                variant=_variant(content, scenario_id),
                ai_line=_DEMO_LINE,
                turn_choices=tuple(dict(choice) for choice in _DEMO_CHOICES),
                chosen_choice_id=chosen,
                target_clue_id=opening[0],
                revealed_clue_ids=opening,
            )
        )

    notices = tuple(
        DemoNotice(level=level, area=area, occurred_at=_past_moment(today, days_ago, _NOTICE_MINUTE))
        for days_ago, level, area in _NOTICE_SCHEDULE
    )
    return DemoPlan(sessions=tuple(sessions), notices=notices)
