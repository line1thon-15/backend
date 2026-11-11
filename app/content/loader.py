"""서버 시작 시 콘텐츠 로드·검증 (T-87 — DECISIONS #107·#111·#118).

검증에 하나라도 실패하면 `ContentValidationError`를 던지고, `create_app`은 시작하지 않는다.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, TypeVar

from pydantic import BaseModel, ValidationError

from app.content.schemas import (
    SAFETY_STOP_MAX_CHARS,
    AiClue,
    AiCluesFile,
    AiScenario,
    AiScenarioFile,
    DiagnosisFile,
    PlatformAppTypesFile,
    SafetyStopFile,
    ScenarioMetaFile,
    ScenarioMetaItem,
)

__all__ = [
    "AREA_IDS",
    "DEFAULT_DATA_DIR",
    "SAFETY_STOP_MAX_CHARS",
    "SUPPORTED_AI_CONTENT_VERSION",
    "ContentBundle",
    "ContentValidationError",
    "ScenarioEntry",
    "load_content",
]

DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"
SUPPORTED_AI_CONTENT_VERSION = "v1"
AREA_IDS: tuple[str, ...] = ("scam", "identity_lending", "friend_pressure")

_ModelT = TypeVar("_ModelT", bound=BaseModel)


class ContentValidationError(Exception):
    """콘텐츠 파일이 규격·참조 무결성을 어김 — 서버를 시작하지 않는다."""


@dataclass(frozen=True)
class ScenarioEntry:
    area: str
    scenario: AiScenario

    @property
    def platform(self) -> str:
        return self.scenario.platform

    @property
    def variation_axes(self):
        return self.scenario.variation_axes


@dataclass(frozen=True)
class ContentBundle:
    area_ids: tuple[str, ...]
    clues: Mapping[str, AiClue]
    scenarios: Mapping[str, ScenarioEntry]
    scenario_meta: Mapping[str, ScenarioMetaItem]
    platform_app_types: PlatformAppTypesFile
    diagnosis: DiagnosisFile
    safety_stop: SafetyStopFile

    @property
    def clue_ids(self) -> frozenset[str]:
        return frozenset(self.clues)

    def app_type_of(self, platform_id: str) -> str:
        for item in self.platform_app_types.platforms:
            if item.platform_id == platform_id:
                return item.app_type
        raise KeyError(platform_id)


def load_content(data_dir: Path = DEFAULT_DATA_DIR) -> ContentBundle:
    data_dir = Path(data_dir)
    ai_dir = data_dir / "ai"

    clues_file = _read(data_dir, ai_dir / "clues.json", AiCluesFile)
    _check_version(clues_file.version, "ai/clues.json")
    _check_areas(clues_file)
    clues = {clue.id: clue for clue in clues_file.clues}
    if len(clues) != len(clues_file.clues):
        raise ContentValidationError("ai/clues.json: duplicate clue id")

    scenarios = _load_scenarios(data_dir, ai_dir, clues)

    meta_file = _read(data_dir, data_dir / "scenario_meta.json", ScenarioMetaFile)
    scenario_meta = _check_scenario_meta(meta_file, scenarios)

    platform_file = _read(
        data_dir, data_dir / "platform_app_types.json", PlatformAppTypesFile
    )
    _check_platform_app_types(platform_file, scenarios)

    diagnosis = _read(data_dir, data_dir / "diagnosis.json", DiagnosisFile)
    _check_diagnosis(diagnosis)

    safety_stop = _read(data_dir, data_dir / "safety_stop.json", SafetyStopFile)

    return ContentBundle(
        area_ids=AREA_IDS,
        clues=MappingProxyType(clues),
        scenarios=MappingProxyType(scenarios),
        scenario_meta=MappingProxyType(scenario_meta),
        platform_app_types=platform_file,
        diagnosis=diagnosis,
        safety_stop=safety_stop,
    )


def _read(data_dir: Path, path: Path, model: type[_ModelT]) -> _ModelT:
    label = path.relative_to(data_dir).as_posix()
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContentValidationError(f"{label}: cannot read file ({exc})") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ContentValidationError(f"{label}: invalid JSON ({exc})") from exc
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise ContentValidationError(f"{label}: {exc}") from exc


def _check_version(version: str, label: str) -> None:
    if version != SUPPORTED_AI_CONTENT_VERSION:
        raise ContentValidationError(
            f"{label}: unsupported version {version!r} "
            f"(expected {SUPPORTED_AI_CONTENT_VERSION!r})"
        )


def _check_areas(clues_file: AiCluesFile) -> None:
    area_ids = [area.id for area in clues_file.areas]
    if sorted(area_ids) != sorted(AREA_IDS):
        raise ContentValidationError(
            f"ai/clues.json: area ids {area_ids} must be exactly {list(AREA_IDS)}"
        )
    for clue in clues_file.clues:
        unknown = [area for area in clue.areas if area not in AREA_IDS]
        if unknown:
            raise ContentValidationError(
                f"ai/clues.json: clue {clue.id!r} has unknown area {unknown}"
            )


def _load_scenarios(
    data_dir: Path, ai_dir: Path, clues: Mapping[str, AiClue]
) -> dict[str, ScenarioEntry]:
    paths = sorted((ai_dir / "scenarios").glob("*.json"))
    if not paths:
        raise ContentValidationError("ai/scenarios: no scenario files")

    scenarios: dict[str, ScenarioEntry] = {}
    for path in paths:
        label = path.relative_to(data_dir).as_posix()
        scenario_file = _read(data_dir, path, AiScenarioFile)
        _check_version(scenario_file.version, label)
        if scenario_file.area not in AREA_IDS:
            raise ContentValidationError(
                f"{label}: unknown area {scenario_file.area!r}"
            )
        if path.stem != scenario_file.area:
            raise ContentValidationError(
                f"{label}: file name must match area {scenario_file.area!r}"
            )
        for scenario in scenario_file.scenarios:
            if scenario.id in scenarios:
                raise ContentValidationError(
                    f"{label}: duplicate scenario id {scenario.id!r}"
                )
            missing = [c.id for c in scenario.clues if c.id not in clues]
            if missing:
                raise ContentValidationError(
                    f"{label}: scenario {scenario.id!r} uses clue ids not in "
                    f"ai/clues.json: {missing}"
                )
            scenarios[scenario.id] = ScenarioEntry(
                area=scenario_file.area, scenario=scenario
            )
    return scenarios


def _check_scenario_meta(
    meta_file: ScenarioMetaFile, scenarios: Mapping[str, ScenarioEntry]
) -> dict[str, ScenarioMetaItem]:
    meta: dict[str, ScenarioMetaItem] = {}
    for item in meta_file.scenarios:
        if item.scenario_id in meta:
            raise ContentValidationError(
                f"scenario_meta.json: duplicate scenario_id {item.scenario_id!r}"
            )
        meta[item.scenario_id] = item

    unknown = sorted(set(meta) - set(scenarios))
    if unknown:
        raise ContentValidationError(
            f"scenario_meta.json: scenario_id not in ai copy: {unknown}"
        )
    missing = sorted(set(scenarios) - set(meta))
    if missing:
        raise ContentValidationError(
            f"scenario_meta.json: scenarios missing from meta: {missing}"
        )
    return meta


def _check_platform_app_types(
    platform_file: PlatformAppTypesFile, scenarios: Mapping[str, ScenarioEntry]
) -> None:
    app_type_ids = [item.id for item in platform_file.app_types]
    if len(set(app_type_ids)) != len(app_type_ids):
        raise ContentValidationError("platform_app_types.json: duplicate app type id")

    mapped: dict[str, str] = {}
    for item in platform_file.platforms:
        if item.platform_id in mapped:
            raise ContentValidationError(
                f"platform_app_types.json: duplicate platform_id {item.platform_id!r}"
            )
        if item.app_type not in app_type_ids:
            raise ContentValidationError(
                f"platform_app_types.json: platform {item.platform_id!r} maps to "
                f"unknown app type {item.app_type!r}"
            )
        mapped[item.platform_id] = item.app_type

    used: set[str] = set()
    for entry in scenarios.values():
        used.add(entry.platform)
        used.update(entry.variation_axes.platform)
    missing = sorted(used - set(mapped))
    if missing:
        raise ContentValidationError(
            f"platform_app_types.json: AI platforms without app type: {missing}"
        )
    unknown = sorted(set(mapped) - used)
    if unknown:
        raise ContentValidationError(
            f"platform_app_types.json: platform_id not used in ai copy: {unknown}"
        )


def _check_diagnosis(diagnosis: DiagnosisFile) -> None:
    question_ids = [q.id for q in diagnosis.questions]
    if len(set(question_ids)) != len(question_ids):
        raise ContentValidationError("diagnosis.json: duplicate question id")
    for question in diagnosis.questions:
        option_ids = [o.id for o in question.options]
        if len(set(option_ids)) != len(option_ids):
            raise ContentValidationError(
                f"diagnosis.json: duplicate option id in question {question.id!r}"
            )

    low = sum(min(o.score for o in q.options) for q in diagnosis.questions)
    high = sum(max(o.score for o in q.options) for q in diagnosis.questions)
    ranges = sorted(diagnosis.difficulty_by_score, key=lambda r: r.min_score)
    expected_next = low
    for item in ranges:
        if item.min_score > item.max_score or item.min_score != expected_next:
            raise ContentValidationError(
                "diagnosis.json: difficulty_by_score must cover "
                f"{low}..{high} without gaps or overlaps"
            )
        expected_next = item.max_score + 1
    if expected_next != high + 1:
        raise ContentValidationError(
            "diagnosis.json: difficulty_by_score must cover "
            f"{low}..{high} without gaps or overlaps"
        )
