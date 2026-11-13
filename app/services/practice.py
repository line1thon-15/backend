"""연습 세션 유스케이스 A15·A16·A17 (T-15)·A18과 A15 다시 도전 (T-16) — Architecture 데이터 흐름 3·4번, "1차 내부 API v1".

- A15: domain이 시나리오(학년 제한)·변형 값(F-12·F-08)을 고름 → `variant` → `start` → 세션·턴 0 저장.
- A16: 본인 세션의 현재 상태.
- A17: 404 → 409 → 422 → 종료 판정(domain) → `turn` 또는 `judge` → 한 트랜잭션 저장(#82·#85).
  safe_reply면 고정 문구 턴으로 멈춤(#99·#113·#118), AI `reply`는 쓰지 않는다.
- A18: 404 → 409(진행 중·멈춤) → `feedback` → V1'~V3' → 카드 level은 domain(#75·#101). 읽기 전용.
- A15 retry: retry_of 본인(404)·종료(409) 확인 → 같은 시나리오·같은 목표 단서, platform·tone 중 1개 이상 다른 변형.
AI 호출·검증이 실패하면 아무것도 저장하지 않고 503 `AI_UNAVAILABLE`.
"""

import logging
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from random import Random
from uuid import UUID

from app.ai_client.ports import (
    AIUnavailableError,
    ClueResult,
    FeedbackRequest,
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
from app.domain.practice_result import (
    CARD_LEVEL_BY_KEY,
    CardLevelUndefined,
    card_level,
    card_level_key,
    has_retry_axes,
)
from app.domain.practice_selection import (
    AxisPair,
    ScenarioCandidate,
    VariantAxes,
    choose_variant_axes,
    draw_scenario,
)
from app.services import practice_validation as check
from app.services.ports import (
    NewCueResult,
    NewPracticeSession,
    NewPracticeTurn,
    PracticeRepository,
    PracticeSessionRecord,
    PracticeStateConflict,
    PracticeTurnRecord,
)

logger = logging.getLogger(__name__)


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


@dataclass(frozen=True)
class CueCardOutput:
    cue_id: str
    label: str
    sentence: str


@dataclass(frozen=True)
class ResultCardOutput:
    level: str
    sentence: str


@dataclass(frozen=True)
class ResultOutput:
    session_id: UUID
    found: tuple[CueCardOutput, ...]
    missed: tuple[CueCardOutput, ...]
    normal_outcome: str | None
    cards: tuple[ResultCardOutput, ...]
    can_retry: bool


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ai_unavailable() -> AppError:
    return AppError(code="AI_UNAVAILABLE", status_code=503, message="AI service is unavailable")


def _session_ended() -> AppError:
    return AppError(code="SESSION_ENDED", status_code=409, message="practice session has ended")


def _session_not_found() -> AppError:
    return AppError(code="SESSION_NOT_FOUND", status_code=404, message="practice session not found")


def _session_not_ended() -> AppError:
    return AppError(code="SESSION_NOT_ENDED", status_code=409, message="practice session has not ended")


def _session_stopped() -> AppError:
    return AppError(code="SESSION_STOPPED", status_code=409, message="practice session was stopped")


def _no_scenario() -> AppError:
    return AppError(code="NO_SCENARIO_AVAILABLE", status_code=409, message="no practice scenario is available")


class PracticeService:
    def __init__(
        self,
        repository: PracticeRepository,
        practice_ai: PracticeAI,
        content: ContentBundle,
        rng_factory: Callable[[], Random] = Random,
        clock: Callable[[], datetime] = _utcnow,
        card_level_by_key: Mapping[str, str] = CARD_LEVEL_BY_KEY,
    ) -> None:
        self._repository = repository
        self._ai = practice_ai
        self._content = content
        self._rng_factory = rng_factory
        self._clock = clock
        # 결과 카드 키→SignalLevel — PRD OQ 63·24 답 전에는 비어 있다(테스트가 주입) (#75)
        self._card_level_by_key = card_level_by_key

    # ---- A15 ------------------------------------------------------------------

    def start_area_session(self, *, child_id: UUID, area: str) -> SessionOutput:
        profile = self._child_profile(child_id)

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
        draw = draw_scenario(
            candidates,
            grade=profile.grade,
            previous=previous,
            preferred_platforms=self._preferred_platforms(profile.favorite_apps),
            rng=self._rng_factory(),
        )
        if draw is None:
            raise _no_scenario()

        entry = self._content.scenarios[draw.scenario_id]
        return self._begin_session(
            child_id=child_id,
            mode="area",
            area=area,
            scenario_id=draw.scenario_id,
            clue_ids=tuple(clue.id for clue in entry.scenario.clues),
            axes=draw.axes,
            previous=previous_pairs.get(draw.scenario_id),
            retry_of=None,
            draw_index=self._repository.count_new_draws(child_id) + 1,
        )

    def start_retry_session(self, *, child_id: UUID, retry_of: UUID) -> SessionOutput:
        """다시 도전 (F-13 ③, F-12): 같은 시나리오·같은 목표 단서, retry_of와 platform·tone 1개 이상 다른 변형."""
        original = self._repository.get_session(retry_of, child_id)
        if original is None:
            raise _session_not_found()
        if original.status == "in_progress":
            raise _session_not_ended()
        if original.status == "stopped":
            # 멈춘 세션은 다시 도전 대상이 아니다 (#113, Tasks T-16)
            raise _session_stopped()
        profile = self._child_profile(child_id)

        entry = self._content.scenarios.get(original.scenario_id)
        if entry is None:
            raise _no_scenario()
        axes_source = entry.variation_axes
        previous = (original.variant["platform"], original.variant["tone"])
        axes = choose_variant_axes(
            ScenarioCandidate(
                scenario_id=original.scenario_id,
                min_grade=None,  # 이미 출제된 시나리오 — 학년 제한은 첫 출제 때 적용됨
                platforms=tuple(axes_source.platform),
                tones=tuple(axes_source.tone),
                contexts=tuple(axes_source.context),
            ),
            previous=AxisPair(platform=previous[0], tone=previous[1]),
            preferred_platforms=self._preferred_platforms(profile.favorite_apps),
            rng=self._rng_factory(),
        )
        if axes is None:
            raise _no_scenario()
        return self._begin_session(
            child_id=child_id,
            mode="retry",
            area=original.area,
            scenario_id=original.scenario_id,
            clue_ids=original.target_cue_ids,
            axes=axes,
            previous=previous,
            retry_of=original.session_id,
            draw_index=None,  # 다시 도전은 새 출제 순번을 쓰지 않는다
        )

    def _child_profile(self, child_id: UUID):
        profile = self._repository.get_child_profile(child_id)
        if profile is None:
            raise AppError(code="UNAUTHENTICATED", status_code=401, message="child authentication is required")
        return profile

    def _preferred_platforms(self, favorite_apps: Sequence[str]) -> frozenset[str]:
        return frozenset(
            item.platform_id
            for item in self._content.platform_app_types.platforms
            if item.app_type in favorite_apps
        )

    def _begin_session(
        self,
        *,
        child_id: UUID,
        mode: str,
        area: str,
        scenario_id: str,
        clue_ids: tuple[str, ...],
        axes: VariantAxes,
        previous: tuple[str, str] | None,
        retry_of: UUID | None,
        draw_index: int | None,
    ) -> SessionOutput:
        """variant → start → 검증 → 세션·턴 0 저장. AI 실패면 아무것도 저장하지 않는다."""
        variant_request = VariantRequest(
            scenario_id=scenario_id,
            platform=axes.platform,
            tone=axes.tone,
            context=axes.context,
        )
        try:
            variant_response = self._ai.variant(variant_request)
            check.check_variant(
                variant_response,
                request=variant_request,
                scenario_clue_ids=clue_ids,
                previous=previous,
            )
            variant = variant_response.variant
            start = self._ai.start(StartRequest(scenario_id=scenario_id, variant=variant))
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
                mode=mode,
                area=area,
                subtype=self._content.scenario_meta[scenario_id].subtype,
                scenario_id=scenario_id,
                is_normal=False,  # 정상 상황 출제는 1차 꺼짐 (#110)
                target_cue_ids=clue_ids,
                variant=variant_json,
                scenario_title=start.title,
                child_setup=start.child_setup,
                ai_role_name=start.ai_role_name,
                draw_index=draw_index,
                started_at=self._clock(),
                retry_of=retry_of,
            ),
            first_turn,
        )
        return SessionOutput(
            session_id=session_id,
            mode=mode,
            area=area,
            is_retry=mode == "retry",
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
            raise _session_ended()
        if record.status == "stopped":
            raise _session_stopped()

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
            try:
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
            except PracticeStateConflict as exc:
                # 같은 세션의 다른 요청이 먼저 저장함 — 이 요청은 끝난 세션에 대한 답 (리뷰 치명 #1)
                raise _session_ended() from exc
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
            try:
                self._repository.record_answer_and_stop(
                    session_id=record.session_id,
                    answered_turn_index=current.turn_index,
                    chosen_choice_id=choice_id,
                    stop_turn=stop_turn,
                    stopped_at=self._clock(),
                )
            except PracticeStateConflict as exc:
                # 같은 세션의 다른 요청이 먼저 저장함 — 이 요청은 끝난 세션에 대한 답 (리뷰 치명 #1)
                raise _session_ended() from exc
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
        try:
            self._repository.record_answer_and_continue(
                session_id=record.session_id,
                answered_turn_index=current.turn_index,
                chosen_choice_id=choice_id,
                next_turn=next_turn,
            )
        except PracticeStateConflict as exc:
            # 같은 세션의 다른 요청이 먼저 저장함 — 이 요청은 끝난 세션에 대한 답 (리뷰 치명 #1)
            raise _session_ended() from exc
        return self._output(record, status="in_progress", turn=next_turn)

    # ---- A18 ------------------------------------------------------------------

    def get_result(self, *, child_id: UUID, session_id: UUID) -> ResultOutput:
        record = self._repository.get_session(session_id, child_id)
        if record is None:
            raise _session_not_found()
        if record.status == "in_progress":
            raise _session_not_ended()
        if record.status == "stopped":
            raise _session_stopped()

        # 404·409 확인 뒤에만 AI를 부른다 (#75 ⑤)
        stored = self._repository.get_cue_results(record.session_id)
        # 카드 level 매핑 확인은 feedback 호출 전 — 값이 없으면 AI 호출 없이 500 (#120, T-89)
        try:
            levels = {
                card_result: self._card_level(record, card_result)
                for card_result in (*set(stored.values()), None)
            }
        except CardLevelUndefined as exc:
            logger.error("practice result card level undefined error_type=%s", type(exc).__name__)
            raise AppError(code="INTERNAL", status_code=500, message="internal server error") from exc
        try:
            response = self._ai.feedback(
                FeedbackRequest(
                    scenario_id=record.scenario_id,
                    # 시나리오 단서 순서 — 저장된 found·missed + 나머지 not_shown (#101)
                    results=[
                        ClueResult(clue_id=clue_id, result=stored.get(clue_id, "not_shown"))
                        for clue_id in record.target_cue_ids
                    ],
                    messages=self._messages(record.turns),
                    variant=Variant.model_validate(record.variant),
                )
            )
            check.check_feedback(response, stored=stored)
        except AIUnavailableError as exc:
            # 부분 응답 없음 — 결과 전체 503 (#75 ⑤)
            raise _ai_unavailable() from exc

        # check_feedback(V3')가 카드 result = 저장된 판정임을 보장 — levels에 항상 있음
        cards = tuple(
            ResultCardOutput(level=levels[card.result], sentence=card.text) for card in response.cards
        ) + (ResultCardOutput(level=levels[None], sentence=response.closing_line),)

        return ResultOutput(
            session_id=record.session_id,
            found=self._cue_cards(record.target_cue_ids, stored, "found"),
            missed=self._cue_cards(record.target_cue_ids, stored, "missed"),
            normal_outcome=record.normal_outcome,
            cards=cards,
            can_retry=self._can_retry(record),
        )

    def _card_level(self, record: PracticeSessionRecord, card_result: str | None) -> str:
        key = card_level_key(
            is_normal=record.is_normal,
            card_result=card_result,
            normal_outcome=record.normal_outcome,
        )
        return card_level(key, self._card_level_by_key)

    def _cue_cards(
        self,
        target_cue_ids: Sequence[str],
        stored: Mapping[str, str],
        outcome: str,
    ) -> tuple[CueCardOutput, ...]:
        """콘텐츠 설명으로만 만든다 — AI 문장을 섞지 않는다 (#101, T-87 clues.json name·description)."""
        return tuple(
            CueCardOutput(
                cue_id=clue_id,
                label=self._content.clues[clue_id].name,
                sentence=self._content.clues[clue_id].description,
            )
            for clue_id in target_cue_ids
            if stored.get(clue_id) == outcome
        )

    def _can_retry(self, record: PracticeSessionRecord) -> bool:
        entry = self._content.scenarios.get(record.scenario_id)
        if entry is None:
            return False
        axes = entry.variation_axes
        return has_retry_axes(
            platforms=axes.platform,
            tones=axes.tone,
            contexts=axes.context,
            current=(record.variant["platform"], record.variant["tone"]),
        )

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
