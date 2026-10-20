"""Tests for curriculum package ingestion tool and validation."""

from pathlib import Path
import pytest

from app.db.database import Database
from app.tools.ingest_curriculum import ingest_curriculum, validate_curriculum_package


def test_validate_valid_package():
    valid_data = {
        "subject": {
            "id": "science",
            "name": "Science",
            "code": "SCI",
            "icon": "Atom",
            "accent_color": "#8B5CF6",
            "display_order": 3,
        },
        "term": 1,
        "chapters": [
            {
                "id": "sci-term1-ch01",
                "chapter_number": 1,
                "title": "Unit 1: Measurements",
                "concepts": [
                    {
                        "id": "sci-ch01-c01",
                        "title": "SI Units",
                        "summary": "Summary here",
                        "key_points": ["Point 1", "Point 2"],
                        "display_order": 1,
                    }
                ],
            }
        ],
    }
    valid, msg = validate_curriculum_package(valid_data, Path("test.json"))
    assert valid is True
    assert msg == "Valid"


def test_validate_package_missing_subject_field():
    invalid_data = {
        "subject": {"id": "science", "name": "Science"},  # missing code, icon, etc.
        "term": 1,
        "chapters": [],
    }
    valid, msg = validate_curriculum_package(invalid_data, Path("invalid.json"))
    assert valid is False
    assert "missing required field" in msg.lower()


def test_validate_package_invalid_term():
    invalid_data = {
        "subject": {
            "id": "science",
            "name": "Science",
            "code": "SCI",
            "icon": "Atom",
            "accent_color": "#8B5CF6",
            "display_order": 3,
        },
        "term": 9,
        "chapters": [],
    }
    valid, msg = validate_curriculum_package(invalid_data, Path("invalid.json"))
    assert valid is False
    assert "invalid term" in msg.lower()


def test_ingest_curriculum_dry_run(tmp_path):
    data_dir = Path(__file__).resolve().parent.parent / "data" / "curriculum"
    db_path = tmp_path / "dry_run.sqlite3"

    stats = ingest_curriculum(db_path, data_dir, dry_run=True)
    assert stats["subjects"] == 4
    assert stats["chapters"] == 24
    assert stats["concepts"] == 28
    # In dry run, database should not be created
    assert not db_path.exists()


def test_ingest_curriculum_into_database(tmp_path):
    data_dir = Path(__file__).resolve().parent.parent / "data" / "curriculum"
    db_path = tmp_path / "actual_ingest.sqlite3"

    stats = ingest_curriculum(db_path, data_dir, dry_run=False, force=True)
    assert stats["subjects"] == 4
    assert stats["chapters"] == 24
    assert stats["concepts"] == 28

    db = Database(db_path)
    subjects = db.list_curriculum_subjects()
    assert len(subjects) == 4
    assert [s["id"] for s in subjects] == ["english", "mathematics", "science", "social_science"]

    math_chapters = db.get_chapters_by_term("mathematics", 1)
    assert len(math_chapters) == 6

    sci_ch1 = db.get_chapter("sci-term1-ch01")
    assert sci_ch1 is not None
    assert len(sci_ch1["concepts"]) >= 1


def test_ingest_missing_directory_raises():
    with pytest.raises(FileNotFoundError):
        ingest_curriculum(Path("dummy.sqlite3"), Path("/nonexistent/directory"))
