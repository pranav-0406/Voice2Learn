"""CLI tool to validate and ingest Class 6 curriculum JSON packages into Voice2Learn SQLite database."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.db.database import Database

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("ingest_curriculum")


def validate_curriculum_package(data: dict[str, Any], filepath: Path) -> tuple[bool, str]:
    """Validate JSON curriculum structure."""
    if "subject" not in data or not isinstance(data["subject"], dict):
        return False, f"{filepath.name}: Missing 'subject' object"
    subj = data["subject"]
    for req in ("id", "name", "code", "icon", "accent_color", "display_order"):
        if req not in subj:
            return False, f"{filepath.name}: Subject missing required field '{req}'"

    if "chapters" not in data or not isinstance(data["chapters"], list):
        return False, f"{filepath.name}: Missing 'chapters' list"

    term = data.get("term", 1)
    if term not in (1, 2, 3):
        return False, f"{filepath.name}: Invalid term '{term}', must be 1, 2, or 3"

    for idx, ch in enumerate(data["chapters"]):
        for ch_req in ("id", "chapter_number", "title"):
            if ch_req not in ch:
                return False, f"{filepath.name}: Chapter #{idx + 1} missing required field '{ch_req}'"

        concepts = ch.get("concepts", [])
        if not isinstance(concepts, list):
            return False, f"{filepath.name}: Chapter '{ch['id']}' concepts must be a list"

        for cidx, c in enumerate(concepts):
            for c_req in ("id", "title", "summary", "key_points", "display_order"):
                if c_req not in c:
                    return False, f"{filepath.name}: Concept #{cidx + 1} in '{ch['id']}' missing '{c_req}'"
            if not isinstance(c["key_points"], list):
                return False, f"{filepath.name}: Concept '{c['id']}' key_points must be a list"

    return True, "Valid"


def ingest_curriculum(
    database_path: Path,
    data_dir: Path,
    dry_run: bool = False,
    force: bool = False,
) -> dict[str, int]:
    """Ingest curriculum JSON files from data_dir into database."""
    if not data_dir.exists():
        raise FileNotFoundError(f"Curriculum data directory not found: {data_dir}")

    json_files = sorted(data_dir.glob("tn_class6_*.json"))
    if not json_files:
        logger.warning(f"No tn_class6_*.json files found in {data_dir}")
        return {"subjects": 0, "chapters": 0, "concepts": 0}

    stats = {"subjects": 0, "chapters": 0, "concepts": 0}
    packages: list[dict[str, Any]] = []

    # Validation pass
    for f in json_files:
        with open(f, "r", encoding="utf-8") as fp:
            try:
                pkg = json.load(fp)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Malformed JSON in {f.name}: {exc}") from exc

        valid, msg = validate_curriculum_package(pkg, f)
        if not valid:
            raise ValueError(f"Curriculum validation error in {f.name}: {msg}")
        packages.append(pkg)

    logger.info(f"Successfully validated {len(packages)} curriculum packages.")

    if dry_run:
        for pkg in packages:
            stats["subjects"] += 1
            stats["chapters"] += len(pkg.get("chapters", []))
            for ch in pkg.get("chapters", []):
                stats["concepts"] += len(ch.get("concepts", []))
        logger.info(f"[DRY RUN] Would ingest: {stats['subjects']} subjects, {stats['chapters']} chapters, {stats['concepts']} concepts.")
        return stats

    db = Database(database_path)
    db.initialize()

    with db.connection() as conn:
        for pkg in packages:
            subj = pkg["subject"]
            term = pkg.get("term", 1)

            # Insert or replace subject
            if force:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO curriculum_subjects
                        (id, name, code, icon, accent_color, display_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        subj["id"],
                        subj["name"],
                        subj["code"],
                        subj["icon"],
                        subj["accent_color"],
                        subj["display_order"],
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO curriculum_subjects
                        (id, name, code, icon, accent_color, display_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        subj["id"],
                        subj["name"],
                        subj["code"],
                        subj["icon"],
                        subj["accent_color"],
                        subj["display_order"],
                    ),
                )
            stats["subjects"] += 1

            for ch in pkg.get("chapters", []):
                if force:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO curriculum_chapters
                            (id, subject_id, term, chapter_number, title, description, textbook_pages, lesson_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            ch["id"],
                            subj["id"],
                            term,
                            ch["chapter_number"],
                            ch["title"],
                            ch.get("description"),
                            ch.get("textbook_pages"),
                            ch.get("lesson_id"),
                        ),
                    )
                else:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO curriculum_chapters
                            (id, subject_id, term, chapter_number, title, description, textbook_pages, lesson_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            ch["id"],
                            subj["id"],
                            term,
                            ch["chapter_number"],
                            ch["title"],
                            ch.get("description"),
                            ch.get("textbook_pages"),
                            ch.get("lesson_id"),
                        ),
                    )
                stats["chapters"] += 1

                for co in ch.get("concepts", []):
                    if force:
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO curriculum_concepts
                                (id, chapter_id, title, summary, key_points_json, display_order)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                co["id"],
                                ch["id"],
                                co["title"],
                                co["summary"],
                                json.dumps(co["key_points"]),
                                co["display_order"],
                            ),
                        )
                    else:
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO curriculum_concepts
                                (id, chapter_id, title, summary, key_points_json, display_order)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                co["id"],
                                ch["id"],
                                co["title"],
                                co["summary"],
                                json.dumps(co["key_points"]),
                                co["display_order"],
                            ),
                        )
                    stats["concepts"] += 1

    logger.info(
        f"Ingestion complete: {stats['subjects']} subjects, "
        f"{stats['chapters']} chapters, {stats['concepts']} concepts."
    )
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Voice2Learn curriculum JSON packages.")
    parser.add_argument("--dry-run", action="store_true", help="Validate without modifying database")
    parser.add_argument("--force", action="store_true", help="Replace existing records instead of ignore")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent / "data" / "curriculum",
        help="Path to curriculum JSON directory",
    )
    args = parser.parse_args()

    settings = get_settings()
    try:
        ingest_curriculum(
            database_path=settings.database_path,
            data_dir=args.data_dir,
            dry_run=args.dry_run,
            force=args.force,
        )
    except Exception as exc:
        logger.error(f"Ingestion failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
