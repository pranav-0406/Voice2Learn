"""Curriculum Entity Resolver for Tamil Nadu Class 6 (English-medium).

Resolves natural language references (e.g., "Science Unit 2", "Math Chapter 1",
"Force and Motion") against real SQLite curriculum records.

Guarantees:
- Never defaults to an unrelated lesson (such as States of Matter) when a unit is requested.
- If a requested unit does not exist, explicitly returns an error detailing available units.
- Supports subject aliases, word numbers ("unit two"), and topic keyword lookups.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.db.database import Database

# Subject normalization aliases
SUBJECT_ALIASES: dict[str, str] = {
    "science": "science",
    "sci": "science",
    "math": "mathematics",
    "maths": "mathematics",
    "mathematics": "mathematics",
    "english": "english",
    "eng": "english",
    "social": "social_science",
    "social science": "social_science",
    "social studies": "social_science",
    "history": "social_science",
    "geography": "social_science",
    "civics": "social_science",
}

# Number words mapping for spoken numbers
WORD_TO_NUMBER: dict[str, int] = {
    "1": 1, "one": 1, "first": 1, "1st": 1,
    "2": 2, "two": 2, "second": 2, "2nd": 2,
    "3": 3, "three": 3, "third": 3, "3rd": 3,
    "4": 4, "four": 4, "fourth": 4, "4th": 4,
    "5": 5, "five": 5, "fifth": 5, "5th": 5,
    "6": 6, "six": 6, "sixth": 6, "6th": 6,
    "7": 7, "seven": 7, "seventh": 7, "7th": 7,
    "8": 8, "eight": 8, "eighth": 8, "8th": 8,
    "9": 9, "nine": 9, "ninth": 9, "9th": 9,
}

# Regex to detect unit/chapter mentions (e.g. "unit 2", "chapter two", "lesson 1", "unit #3")
UNIT_PATTERN = re.compile(
    r"\b(?:unit|chapter|lesson)\s*(?:#|no\.?|number)?\s*([a-z0-9]+)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ResolvedCurriculum:
    """Structured resolution of a requested curriculum entity."""
    found: bool
    subject_id: str | None = None
    subject_name: str | None = None
    chapter_id: str | None = None
    chapter_title: str | None = None
    chapter_number: int | None = None
    description: str | None = None
    concept_count: int = 0
    first_concept_id: str | None = None
    first_concept_title: str | None = None
    concept_id: str | None = None
    lesson_id: str | None = None
    target_url: str | None = None
    error: str | None = None
    available_units: int = 0


class CurriculumResolver:
    """Resolves subject and chapter/unit requests against SQLite curriculum data."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def resolve(
        self,
        query: str | None = None,
        subject: str | None = None,
        unit_number: int | None = None,
        term: int = 1,
    ) -> ResolvedCurriculum:
        """Resolve a curriculum entity from explicit parameters or natural query text."""
        target_subject = self._normalize_subject(subject) if subject else None
        target_unit = unit_number

        # If natural query is provided, extract subject and unit number
        if query:
            extracted_sub, extracted_unit = self._extract_entities_from_query(query)
            if not target_subject:
                target_subject = extracted_sub
            if target_unit is None:
                target_unit = extracted_unit

        # Case 1: Neither subject nor query provided
        if not target_subject and not query:
            return ResolvedCurriculum(
                found=False,
                error="Please specify a subject (Science, Mathematics, English, or Social Science).",
            )

        # Case 2: Subject is identified
        if target_subject:
            subj_meta = self.database.get_curriculum_subject(target_subject)
            if not subj_meta:
                return ResolvedCurriculum(
                    found=False,
                    error=f"Subject '{target_subject}' does not exist in the curriculum.",
                )

            chapters = self.database.get_chapters_by_term(target_subject, term)
            total_units = len(chapters)

            # If unit number is specified:
            if target_unit is not None:
                chapter = self.database.get_chapter_by_unit(target_subject, target_unit, term)
                if not chapter:
                    return ResolvedCurriculum(
                        found=False,
                        subject_id=target_subject,
                        subject_name=subj_meta["name"],
                        available_units=total_units,
                        error=(
                            f"{subj_meta['name']} has {total_units} units in Term {term}. "
                            f"Unit {target_unit} does not exist."
                        ),
                    )
                return self._build_resolved_chapter(subj_meta, chapter)

            # If no unit number specified, check if query matches a chapter title/topic
            if query:
                matched_chap = self.database.find_chapter_by_title(query, target_subject)
                if matched_chap:
                    return self._build_resolved_chapter(subj_meta, matched_chap)

            # Subject only requested (e.g. "Open Science"): navigate to first unit
            if chapters:
                first_chap = self.database.get_chapter(chapters[0]["id"])
                if first_chap:
                    return self._build_resolved_chapter(subj_meta, first_chap)

            return ResolvedCurriculum(
                found=False,
                subject_id=target_subject,
                subject_name=subj_meta["name"],
                error=f"No chapters found for {subj_meta['name']} in Term {term}.",
            )

        # Case 3: Query without explicit subject - try title match across all subjects
        if query:
            matched_chap = self.database.find_chapter_by_title(query)
            if matched_chap:
                subj_meta = self.database.get_curriculum_subject(matched_chap["subject_id"])
                if subj_meta:
                    return self._build_resolved_chapter(subj_meta, matched_chap)

        return ResolvedCurriculum(
            found=False,
            error="Could not identify the requested subject or unit in our Class 6 curriculum.",
        )

    def _build_resolved_chapter(
        self, subj_meta: dict[str, Any], chapter: dict[str, Any]
    ) -> ResolvedCurriculum:
        """Construct the resolved payload with correct deep-link URL."""
        concepts = chapter.get("concepts", [])
        first_concept_id: str | None = None
        first_concept_title: str | None = None
        target_url: str

        if concepts:
            first_concept = concepts[0]
            first_concept_id = first_concept["id"]
            first_concept_title = first_concept["title"]
            target_url = f"/concept/{first_concept_id}"
        elif chapter.get("lesson_id"):
            target_url = f"/lesson/{chapter['lesson_id']}"
        else:
            target_url = f"/dashboard?subject={subj_meta['id']}"

        return ResolvedCurriculum(
            found=True,
            subject_id=subj_meta["id"],
            subject_name=subj_meta["name"],
            chapter_id=chapter["id"],
            chapter_title=chapter["title"],
            chapter_number=chapter["chapter_number"],
            description=chapter.get("description"),
            concept_count=len(concepts),
            first_concept_id=first_concept_id,
            first_concept_title=first_concept_title,
            concept_id=first_concept_id,
            lesson_id=chapter.get("lesson_id"),
            target_url=target_url,
        )

    def _normalize_subject(self, subject: str) -> str | None:
        """Map text to recognized subject id."""
        cleaned = subject.strip().lower()
        return SUBJECT_ALIASES.get(cleaned)

    def _extract_entities_from_query(self, query: str) -> tuple[str | None, int | None]:
        """Extract subject and unit/chapter number from natural language input."""
        q_lower = query.lower()

        # 1. Extract subject
        subject: str | None = None
        # Check longer phrases first ("social science" before "social")
        for alias, sub_id in sorted(SUBJECT_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
            if re.search(r"\b" + re.escape(alias) + r"\b", q_lower):
                subject = sub_id
                break

        # 2. Extract unit/chapter number
        unit_number: int | None = None
        unit_match = UNIT_PATTERN.search(q_lower)
        if unit_match:
            num_token = unit_match.group(1).lower()
            if num_token in WORD_TO_NUMBER:
                unit_number = WORD_TO_NUMBER[num_token]
            elif num_token.isdigit():
                unit_number = int(num_token)

        return subject, unit_number
