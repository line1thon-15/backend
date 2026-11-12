"""연습 세션 유스케이스 A15·A16·A17 (T-15 — Architecture 데이터 흐름 3번, "1차 내부 API v1").

- A15: domain이 시나리오(학년 제한)·변형 값(F-12·F-08)을 고름 → `variant` → `start` → 세션·턴 0 저장.
- A16: 본인 세션의 현재 상태.
- A17: 404 → 409 → 422 → 종료 판정(domain) → `turn` 또는 `judge` → 한 트랜잭션 저장(#82·#85).
  safe_reply면 고정 문구 턴으로 멈춤(#99·#113·#118), AI `reply`는 쓰지 않는다.
AI 호출·검증이 실패하면 아무것도 저장하지 않고 503 `AI_UNAVAILABLE`.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from random import Random
from uuid import UUID

from app.ai_client.ports import (
    AIUnavailableError,
    JudgeRequest,
    Message,
    PracticeAI,
    StartRequest,
    TurnRequest,
    Variant,
    VariantRequest,
)
from app.content.loader import ContentBundle
from app.core.errors import AppError
from app.domain.practice_end import is_practice_over
from app.domain.practice_selection import AxisPair, ScenarioCandidate, draw_scenario
from app.services import practice_validation as check
from app.services.ports import (
    NewCueResult,
    NewPracticeSession,
    NewPracticeTurn,
    PracticeRepository,
    PracticeSessionRecord,
    PracticeTurnRecord,
)


@dataclass(frozen=True)
class TurnOutput:
    turn_index: int
    speaker_name: str
    platform: str
    ai_line: str
    choices: tuple[tuple[str, str], ...]  # (id, text) — kind는 내보내지 않는다
    substituted: bool


@dataclass(frozen=True)
class SessionOutput:
    session_id: UUID
    mode: str
    area: str
    is_retry: bool
    status: str
    turn: TurnOutput | None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ai_unavailable() -> AppError:
    return AppError(code="AI_UNAVAILABLE", status_code=503, message="AI service is unavailable")


def _session_not_found() -> AppError:
    return AppError(code="SESSION_NOT_FOUND", status_code=404, message="practice session not found")


class PracticeService:
    def __init__(
        self,
        repository: PracticeRepository,
        practice_ai: PracticeAI,
        content: ContentBundle,
        rng_factory: Callable[[], Random] = Random,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._repository = repository
        self._ai = practice_ai
        self._content = content
        self._rng_factory = rng_factory
        self._clock = clock

    # ---- A15 ------------------------------------------------------------------

    def start_area_session(self, *, child_id: UUID, area: str) -> SessionOutput:
        profile = self._repository.get_child_profile(child_id)
        if profile is None:
            raise AppError(code="UNAUTHENTICATED", status_code=401, message="child authentication is required")

        candidates = [
            ScenarioCandidate(
                scenario_id=scenario_id,
                min_grade=self._content.scenario_meta[scenario_id].min_grade,
                platforms=tuple(entry.variation_axes.platform),
                tones=tuple(entry.variation_axes.tone),
                contexts=tuple(entry.variation_axes.context),
            )
            for scenario_id, entry in self._content.scenarios.items()
            if entry.area == area
        ]
        previous_pairs = self._repository.latest_variant_axes(
            child_id, [candidate.scenario_id for candidate in candidates]
        )
        previous = {sid: AxisPair(platform=p, tone=t) for sid, (p, t) in previous_pairs.items()}
        preferred_platforms = frozenset(
            item.platform_id
            for item in self._content.platform_app_types.platforms
            if item.app_type in profile.favorite_apps
        )
        draw = draw_scenario(
            candidates,
            grade=profile.grade,
            previous=previous,
            preferred_platforms=preferred_platforms,
            rng=self._rng_factory(),
        )
        if draw is None:
            raise AppError(
                code="NO_SCENARIO_AVAILABLE",
                status_code=409,
                message="no practice scenario is available",
            )

        entry = self._content.scenarios[draw.scenario_id]
        clue_ids = tuple(clue.id for clue in entry.scenario.clues)
        variant_request = VariantRequest(
            scenario_id=draw.scenario_id,
            platform=draw.axes.platform,
            tone=draw.axes.tone,
            context=draw.axes.context,
        )
        try:
            variant_response = self._ai.variant(variant_request)
            check.check_variant(
                variant_response,
                request=variant_request,
                scenario_clue_ids=clue_ids,
                previous=previous_pairs.get(draw.scenario_id),
            )
            variant = variant_response.variant
            start = self._ai.start(StartRequest(scenario_id=draw.scenario_id, variant=variant))
            check.check_start(start, scenario_clue_ids=clue_ids)
        except AIUnavailableError as exc:
            raise _ai_unavailable() from exc

        first_turn = NewPracticeTurn(
            turn_index=0,
            ai_line=start.reply,
            choices=tuple(self._choice_dicts(start.choices)),
            substituted=False,
            target_clue_id=start.target_clue_id,
            revealed_clue_ids=tuple(start.revealed_clue_ids),
            ai_status="ok",
        )
        variant_json = variant.model_dump(mode="json")
        session_id = self._repository.create_session(
            NewPracticeSession(
                child_id=child_id,
                mode="area",
                area=area,
                subtype=self._content.scenario_meta[draw.scenario_id].subtype,
                scenario_id=draw.scenario_id,
                is_normal=False,  # 정상 상황 출제는 1차 꺼짐 (#110)
                target_cue_ids=clue_ids,
                variant=variant_json,
                scenario_title=start.title,
                child_setup=start.child_setup,
                ai_role_name=start.ai_role_name,
                draw_index=self._repository.count_new_draws(child_id) + 1,
                started_at=self._clock(),
            ),
            first_turn,
        )
        return SessionOutput(
            session_id=session_id,
            mode="area",
            area=area,
            is_retry=False,
            status="in_progress",
            turn=self._turn_output(first_turn, ai_role_name=start.ai_role_name, variant=variant_json),
        )

    # ---- A16 ------------------------------------------------------------------

    def get_session(self, *, child_id: UUID, session_id: UUID) -> SessionOutput:
        record = self._repository.get_session(session_id, child_id)
        if record is None:
            raise _session_not_found()
        return self._session_output(record)

    # ---- A17 ------------------------------------------------------------------

    def answer(self, *, child_id: UUID, session_id: UUID, choice_id: str) -> SessionOutput:
        record = self._repository.get_session(session_id, child_id)
        if record is None:
            raise _session_not_found()
        if record.status == "ended":
            raise AppError(code="SESSION_ENDED", status_code=409, message="practice session has ended")
        if record.status == "stopped":
            raise AppError(code="SESSION_STOPPED", status_code=409, message="practice session was stopped")

        current = record.turns[-1]
        chosen = next((choice for choice in current.choices if choice["id"] == choice_id), None)
        if chosen is None:
            raise AppError(code="INVALID_CHOICE", status_code=422, message="choice is not in the current turn")

        answer_count = current.turn_index + 1
        clue_ids = record.target_cue_ids
        variant = Variant.model_validate(record.variant)
        messages = self._messages(record.turns[:-1]) + [
            Message(role="ai", text=current.ai_line),
            Message(
                role="child",
                text=chosen["text"],
                choice_kind=chosen["kind"],
                clue_id=current.target_clue_id,
            ),
        ]
        sent_revealed = list(current.revealed_clue_ids)

        if is_practice_over(is_normal=record.is_normal, kind=chosen["kind"], answer_count=answer_count):
            try:
                judged = self._ai.judge(
                    JudgeRequest(
                        scenario_id=record.scenario_id,
                        messages=messages,
                        revealed_clue_ids=sent_revealed,
                        variant=variant,
                    )
                )
                check.check_judge(
                    judged,
                    scenario_clue_ids=clue_ids,
                    sent_revealed=sent_revealed,
                    messages=messages,
                )
            except AIUnavailableError as exc:
                raise _ai_unavailable() from exc
            self._repository.record_answer_and_end(
                session_id=record.session_id,
                child_id=child_id,
                answered_turn_index=current.turn_index,
                chosen_choice_id=choice_id,
                # not_shown은 저장하지 않는다 (#109)
                cue_results=[
                    NewCueResult(cue_id=item.clue_id, outcome=item.result)
                    for item in judged.results
                    if item.result != "not_shown"
                ],
                ended_at=self._clock(),
            )
            return self._output(record, status="ended", turn=None)

        try:
            response = self._ai.turn(
                TurnRequest(
                    scenario_id=record.scenario_id,
                    messages=messages,
                    revealed_clue_ids=sent_revealed,
                    variant=variant,
                )
            )
            if response.status != "safe_reply":
                check.check_turn(response, sent_revealed=sent_revealed, scenario_clue_ids=clue_ids)
        except AIUnavailableError as exc:
            raise _ai_unavailable() from exc

        if response.status == "safe_reply":
            # AI reply·나머지 필드는 읽지도 저장하지도 않는다 — 고정 문구 스냅숏 (#118)
            stop_turn = NewPracticeTurn(
                turn_index=current.turn_index + 1,
                ai_line=self._content.safety_stop.message,
                choices=(),
                substituted=False,
                target_clue_id=None,
                revealed_clue_ids=tuple(sent_revealed),
                ai_status="safe_reply",
            )
            self._repository.record_answer_and_stop(
                session_id=record.session_id,
                answered_turn_index=current.turn_index,
                chosen_choice_id=choice_id,
                stop_turn=stop_turn,
                stopped_at=self._clock(),
            )
            return self._output(record, status="stopped", turn=stop_turn)

        next_turn = NewPracticeTurn(
            turn_index=current.turn_index + 1,
            ai_line=response.reply,
            choices=tuple(self._choice_dicts(response.choices)),
            substituted=response.status == "blocked" or response.source in ("fallback", "fixed"),
            target_clue_id=response.target_clue_id,
            revealed_clue_ids=tuple(response.revealed_clue_ids),
            ai_status=response.status,
        )
        self._repository.record_answer_and_continue(
            session_id=record.session_id,
            answered_turn_index=current.turn_index,
            chosen_choice_id=choice_id,
            next_turn=next_turn,
        )
        return self._output(record, status="in_progress", turn=next_turn)

    # ---- 변환 ----------------------------------------------------------------

    @staticmethod
    def _choice_dicts(choices) -> list[dict]:
        return [{"id": choice.id, "text": choice.text, "kind": choice.kind} for choice in choices]

    @staticmethod
    def _messages(turns: tuple[PracticeTurnRecord, ...]) -> list[Message]:
        """상태 재구성(#98): 턴 행 순서대로 AI 대사 → 그 턴에 고른 답."""
        messages: list[Message] = []
        for turn in turns:
            messages.append(Message(role="ai", text=turn.ai_line))
            chosen = next(choice for choice in turn.choices if choice["id"] == turn.chosen_choice_id)
            messages.append(
                Message(
                    role="child",
                    text=chosen["text"],
                    choice_kind=chosen["kind"],
                    clue_id=turn.target_clue_id,
                )
            )
        return messages

    @staticmethod
    def _turn_output(
        turn: NewPracticeTurn | PracticeTurnRecord,
        *,
        ai_role_name: str,
        variant: dict,
    ) -> TurnOutput:
        return TurnOutput(
            turn_index=turn.turn_index,
            speaker_name=ai_role_name,
            platform=variant["platform"],
            ai_line=turn.ai_line,
            choices=tuple((choice["id"], choice["text"]) for choice in turn.choices),
            substituted=turn.substituted,
        )

    def _output(
        self,
        record: PracticeSessionRecord,
        *,
        status: str,
        turn: NewPracticeTurn | PracticeTurnRecord | None,
    ) -> SessionOutput:
        return SessionOutput(
            session_id=record.session_id,
            mode=record.mode,
            area=record.area,
            is_retry=record.mode == "retry",
            status=status,
            turn=(
                self._turn_output(turn, ai_role_name=record.ai_role_name, variant=record.variant)
                if turn is not None
                else None
            ),
        )

    def _session_output(self, record: PracticeSessionRecord) -> SessionOutput:
        # in_progress = 답할 현재 턴, stopped = 안내 턴, ended = 턴 없음 (#82·#99)
        turn = None if record.status == "ended" else record.turns[-1]
        return self._output(record, status=record.status, turn=turn)
