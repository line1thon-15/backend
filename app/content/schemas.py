"""콘텐츠 파일의 Pydantic 규격 (T-87, Architecture "콘텐츠 파일 규격").

- AI 사본(`data/ai/`)은 ai 저장소 소유라 백엔드가 쓰는 필드만 검증하고 나머지 필드는 무시한다.
- 백엔드 보충 파일은 모르는 필드를 거부한다(`note`는 예시 데이터 표시용 설명).
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

GradeId = Literal["E6", "M1", "M2", "M3", "H1", "H2", "H3"]
ScamSubtype = Literal["game_item", "allowance", "high_paying_job"]

SAFETY_STOP_MAX_CHARS = 300


class _AiModel(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


class _BackendModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# ---- AI 사본 ---------------------------------------------------------------


class AiArea(_AiModel):
    id: str
    name: str


class AiClue(_AiModel):
    id: str
    areas: list[str] = Field(min_length=1)
    name: str
    description: str
    safe_action: str


class AiCluesFile(_AiModel):
    version: str
    areas: list[AiArea]
    clues: list[AiClue] = Field(min_length=1)


class AiScenarioClue(_AiModel):
    id: str
    at_opening: bool = False
    reveal_when: str
    reveal_line: str


class AiVariationAxes(_AiModel):
    platform: list[str] = Field(min_length=1)
    tone: list[str] = Field(min_length=1)
    context: list[str] = Field(min_length=1)


class AiScenario(_AiModel):
    id: str
    title: str
    platform: str
    difficulty: int
    clues: list[AiScenarioClue] = Field(min_length=1)
    variation_axes: AiVariationAxes
    normal_situations: list[dict] = Field(default_factory=list)


class AiScenarioFile(_AiModel):
    version: str
    area: str
    scenarios: list[AiScenario] = Field(min_length=1)


# ---- 백엔드 보충 파일 ---------------------------------------------------------


class ScenarioMetaItem(_BackendModel):
    scenario_id: str
    subtype: ScamSubtype | None
    min_grade: GradeId | None


class ScenarioMetaFile(_BackendModel):
    version: str
    note: str | None = None
    scenarios: list[ScenarioMetaItem]


class AppType(_BackendModel):
    id: str
    label: str


class PlatformAppType(_BackendModel):
    platform_id: str
    app_type: str


class PlatformAppTypesFile(_BackendModel):
    version: str
    note: str | None = None
    app_types: list[AppType] = Field(min_length=1)
    platforms: list[PlatformAppType]


class DiagnosisOption(_BackendModel):
    id: str
    text: str
    score: int = Field(ge=0)


class DiagnosisQuestion(_BackendModel):
    id: str
    text: str
    options: list[DiagnosisOption] = Field(min_length=2)


class DifficultyRange(_BackendModel):
    min_score: int = Field(ge=0)
    max_score: int = Field(ge=0)
    difficulty: int = Field(ge=1)


class DiagnosisFile(_BackendModel):
    note: str | None = None
    questions: list[DiagnosisQuestion] = Field(min_length=3, max_length=3)
    difficulty_by_score: list[DifficultyRange] = Field(min_length=1)


class SafetyStopFile(_BackendModel):
    version: str
    note: str | None = None
    message: str = Field(max_length=SAFETY_STOP_MAX_CHARS)

    @field_validator("message")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value
