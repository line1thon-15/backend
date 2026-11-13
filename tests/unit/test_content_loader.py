"""T-87 콘텐츠 사본·보충 파일의 서버 시작 시 검증 (DECISIONS #107·#111·#118).

임시 fixture는 pytest `tmp_path`(OS 임시 디렉터리)에 실제 데이터 폴더를 복사해 만들고,
pytest가 실행 종료 후 정리한다.
"""

import hashlib
import json
import re
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).resolve().parents[2] / "app" / "content" / "data"
AI_DIR = DATA_DIR / "ai"


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    target = tmp_path / "data"
    shutil.copytree(DATA_DIR, target)
    return target


def _edit(path: Path, change: Callable[[dict], None]) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _load(path: Path):
    from app.content.loader import load_content

    return load_content(path)


def _expect_failure(path: Path, pattern: str) -> None:
    from app.content.loader import ContentValidationError

    with pytest.raises(ContentValidationError, match=pattern):
        _load(path)


# ---- 정상 ----------------------------------------------------------------


def test_real_content_loads_with_expected_areas_and_scenarios() -> None:
    content = _load(DATA_DIR)

    assert content.area_ids == ("scam", "identity_lending", "friend_pressure")
    assert set(content.scenarios) == {"scam_dm_parttime_01", "scam_jobboard_link_01"}
    assert content.scenarios["scam_dm_parttime_01"].area == "scam"
    assert "too_good_pay" in content.clue_ids
    assert set(content.scenario_meta) == set(content.scenarios)
    assert content.safety_stop.message.strip() != ""
    assert len(content.diagnosis.questions) == 3


def test_high_paying_job_scenarios_are_limited_to_high_school() -> None:
    content = _load(DATA_DIR)

    for scenario_id, meta in content.scenario_meta.items():
        if meta.subtype == "high_paying_job":
            assert meta.min_grade == "H1", scenario_id


def test_every_scenario_platform_has_an_app_type() -> None:
    content = _load(DATA_DIR)
    app_type_ids = {item.id for item in content.platform_app_types.app_types}

    for scenario in content.scenarios.values():
        for platform in {scenario.platform, *scenario.variation_axes.platform}:
            assert content.app_type_of(platform) in app_type_ids


def test_ai_copy_matches_pinned_source_hashes() -> None:
    source = (AI_DIR / "SOURCE.txt").read_text(encoding="utf-8")
    assert "331d2c63481ea212105c466caba86a28acd9dea7" in source
    lf_section = source.split("SHA-256 (LF 기준", 1)[1].split("참고 —", 1)[0]
    expected = dict(
        (name, digest)
        for digest, name in re.findall(r"^([0-9a-f]{64}) \*(\S+)$", lf_section, re.M)
    )

    assert set(expected) == {"clues.json", "scenarios/scam.json"}
    for name, digest in expected.items():
        raw = (AI_DIR / name).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(raw).hexdigest() == digest, name


def test_legacy_backend_content_files_are_not_created() -> None:
    for legacy in ("cues.json", "scenarios.json", "variants.json"):
        assert not (DATA_DIR / legacy).exists(), legacy
        assert not (AI_DIR / legacy).exists(), legacy


def test_safety_stop_message_at_max_length_is_accepted(data_dir: Path) -> None:
    from app.content.loader import SAFETY_STOP_MAX_CHARS

    assert SAFETY_STOP_MAX_CHARS == 300
    _edit(data_dir / "safety_stop.json", lambda d: d.update(message="가" * 300))

    assert _load(data_dir).safety_stop.message == "가" * 300


# ---- version ---------------------------------------------------------------


def test_unsupported_clues_version_fails(data_dir: Path) -> None:
    _edit(data_dir / "ai" / "clues.json", lambda d: d.update(version="v2"))
    _expect_failure(data_dir, "version")


def test_unsupported_scenario_file_version_fails(data_dir: Path) -> None:
    _edit(data_dir / "ai" / "scenarios" / "scam.json", lambda d: d.update(version="v0"))
    _expect_failure(data_dir, "version")


# ---- 단서 참조 --------------------------------------------------------------


def test_scenario_clue_not_in_clues_fails(data_dir: Path) -> None:
    def change(d: dict) -> None:
        d["scenarios"][0]["clues"][0]["id"] = "unknown_clue"

    _edit(data_dir / "ai" / "scenarios" / "scam.json", change)
    _expect_failure(data_dir, "unknown_clue")


def test_duplicate_scenario_id_fails(data_dir: Path) -> None:
    def change(d: dict) -> None:
        d["scenarios"][1]["id"] = d["scenarios"][0]["id"]

    _edit(data_dir / "ai" / "scenarios" / "scam.json", change)
    _expect_failure(data_dir, "scam_dm_parttime_01")


# ---- scenario_meta ----------------------------------------------------------


def test_scenario_meta_with_unknown_scenario_fails(data_dir: Path) -> None:
    def change(d: dict) -> None:
        d["scenarios"].append(
            {"scenario_id": "ghost_01", "subtype": None, "min_grade": None}
        )

    _edit(data_dir / "scenario_meta.json", change)
    _expect_failure(data_dir, "ghost_01")


def test_scenario_missing_from_meta_fails(data_dir: Path) -> None:
    def change(d: dict) -> None:
        d["scenarios"] = [
            item for item in d["scenarios"] if item["scenario_id"] != "scam_jobboard_link_01"
        ]

    _edit(data_dir / "scenario_meta.json", change)
    _expect_failure(data_dir, "scam_jobboard_link_01")


def test_scenario_meta_invalid_grade_fails(data_dir: Path) -> None:
    def change(d: dict) -> None:
        d["scenarios"][0]["min_grade"] = "M9"

    _edit(data_dir / "scenario_meta.json", change)
    _expect_failure(data_dir, "min_grade")


# ---- 영역 ID ----------------------------------------------------------------


def test_missing_area_in_clues_fails(data_dir: Path) -> None:
    def change(d: dict) -> None:
        d["areas"] = [a for a in d["areas"] if a["id"] != "friend_pressure"]

    _edit(data_dir / "ai" / "clues.json", change)
    _expect_failure(data_dir, "area")


def test_extra_area_in_clues_fails(data_dir: Path) -> None:
    def change(d: dict) -> None:
        d["areas"].append({"id": "bullying", "name": "따돌림"})

    _edit(data_dir / "ai" / "clues.json", change)
    _expect_failure(data_dir, "bullying")


def test_clue_with_unknown_area_fails(data_dir: Path) -> None:
    def change(d: dict) -> None:
        d["clues"][0]["areas"] = ["identity"]

    _edit(data_dir / "ai" / "clues.json", change)
    _expect_failure(data_dir, "identity")


def test_scenario_file_with_unknown_area_fails(data_dir: Path) -> None:
    _edit(data_dir / "ai" / "scenarios" / "scam.json", lambda d: d.update(area="fraud"))
    _expect_failure(data_dir, "fraud")


# ---- safety_stop -------------------------------------------------------------


@pytest.mark.parametrize("message", ["", "   \n\t "])
def test_blank_safety_stop_message_fails(data_dir: Path, message: str) -> None:
    _edit(data_dir / "safety_stop.json", lambda d: d.update(message=message))
    _expect_failure(data_dir, "safety_stop")


def test_safety_stop_message_over_max_length_fails(data_dir: Path) -> None:
    _edit(data_dir / "safety_stop.json", lambda d: d.update(message="가" * 301))
    _expect_failure(data_dir, "safety_stop")


def test_missing_safety_stop_file_fails(data_dir: Path) -> None:
    (data_dir / "safety_stop.json").unlink()
    _expect_failure(data_dir, "safety_stop.json")


# ---- platform_app_types -----------------------------------------------------


def test_scenario_platform_without_app_type_fails(data_dir: Path) -> None:
    def change(d: dict) -> None:
        d["platforms"] = [p for p in d["platforms"] if p["platform_id"] != "job_board"]

    _edit(data_dir / "platform_app_types.json", change)
    _expect_failure(data_dir, "job_board")


def test_platform_mapped_to_unknown_app_type_fails(data_dir: Path) -> None:
    def change(d: dict) -> None:
        d["platforms"][0]["app_type"] = "no_such_app"

    _edit(data_dir / "platform_app_types.json", change)
    _expect_failure(data_dir, "no_such_app")


# ---- diagnosis ---------------------------------------------------------------


def test_diagnosis_with_two_questions_fails(data_dir: Path) -> None:
    _edit(data_dir / "diagnosis.json", lambda d: d.update(questions=d["questions"][:2]))
    _expect_failure(data_dir, "questions")


def test_diagnosis_score_range_gap_fails(data_dir: Path) -> None:
    def change(d: dict) -> None:
        d["difficulty_by_score"] = d["difficulty_by_score"][1:]

    _edit(data_dir / "diagnosis.json", change)
    _expect_failure(data_dir, "difficulty_by_score")


# ---- 파일 형식 ---------------------------------------------------------------


def test_invalid_json_fails(data_dir: Path) -> None:
    (data_dir / "ai" / "clues.json").write_text("{not json", encoding="utf-8")
    _expect_failure(data_dir, "clues.json")


def test_missing_scenarios_folder_content_fails(data_dir: Path) -> None:
    (data_dir / "ai" / "scenarios" / "scam.json").unlink()
    _expect_failure(data_dir, "scenarios")


# ---- 서버 시작 ---------------------------------------------------------------


def test_create_app_loads_content_into_state(sqlite_url: str) -> None:
    from app.core.config import Settings
    from app.main import create_app

    app = create_app(Settings(_env_file=None, database_url=sqlite_url, ai_client="fake"))
    try:
        assert set(app.state.content.scenarios) == {
            "scam_dm_parttime_01",
            "scam_jobboard_link_01",
        }
    finally:
        app.state.engine.dispose()


def test_create_app_refuses_to_start_with_invalid_content(
    data_dir: Path, sqlite_url: str
) -> None:
    from app.content.loader import ContentValidationError
    from app.core.config import Settings
    from app.main import create_app

    _edit(data_dir / "safety_stop.json", lambda d: d.update(message=" "))

    with pytest.raises(ContentValidationError):
        create_app(
            Settings(_env_file=None, database_url=sqlite_url, ai_client="fake"),
            content_dir=data_dir,
        )
