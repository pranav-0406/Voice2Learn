"""Small SQLite data access layer for learners and seeded lessons."""

from __future__ import annotations

import json
import math
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.db.curriculum_seed import CURRICULUM_CHAPTERS, CURRICULUM_CONCEPTS, CURRICULUM_SUBJECTS
from app.db.seed import ALL_LESSONS, ALL_QUESTIONS


class Database:
    """Owns short-lived SQLite connections and the prototype's SQL queries."""

    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS learners (
                    id TEXT PRIMARY KEY,
                    nickname TEXT NOT NULL,
                    grade_band TEXT NOT NULL CHECK (grade_band IN ('6-7', '8-9')),
                    created_at TEXT NOT NULL,
                    ability REAL NOT NULL DEFAULT 1000,
                    points INTEGER NOT NULL DEFAULT 0,
                    correct_streak INTEGER NOT NULL DEFAULT 0,
                    incorrect_streak INTEGER NOT NULL DEFAULT 0,
                    target_difficulty TEXT NOT NULL DEFAULT 'medium'
                );
                CREATE TABLE IF NOT EXISTS lessons (
                    id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    subject_name TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS questions (
                    id TEXT PRIMARY KEY,
                    lesson_id TEXT NOT NULL REFERENCES lessons(id),
                    subject_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    difficulty TEXT NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
                    rating INTEGER NOT NULL,
                    prompt TEXT NOT NULL,
                    choices_json TEXT NOT NULL,
                    accepted_answers_json TEXT NOT NULL,
                    hint TEXT,
                    explanation TEXT,
                    concept_id TEXT
                );
                CREATE TABLE IF NOT EXISTS attempts (
                    id TEXT PRIMARY KEY,
                    learner_id TEXT NOT NULL REFERENCES learners(id),
                    question_id TEXT NOT NULL REFERENCES questions(id),
                    submitted_answer TEXT NOT NULL,
                    is_correct INTEGER NOT NULL CHECK (is_correct IN (0, 1)),
                    points_awarded INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE (learner_id, question_id)
                );
                CREATE TABLE IF NOT EXISTS learner_topic_progress (
                    learner_id TEXT NOT NULL REFERENCES learners(id),
                    topic TEXT NOT NULL,
                    attempts_count INTEGER NOT NULL DEFAULT 0,
                    correct_count INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (learner_id, topic)
                );
                CREATE TABLE IF NOT EXISTS learner_lesson_progress (
                    learner_id TEXT NOT NULL REFERENCES learners(id),
                    lesson_id TEXT NOT NULL REFERENCES lessons(id),
                    attempts_count INTEGER NOT NULL DEFAULT 0,
                    correct_count INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (learner_id, lesson_id)
                );
                CREATE TABLE IF NOT EXISTS curriculum_subjects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    code TEXT NOT NULL UNIQUE,
                    icon TEXT NOT NULL,
                    accent_color TEXT NOT NULL,
                    display_order INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS curriculum_chapters (
                    id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL REFERENCES curriculum_subjects(id),
                    term INTEGER NOT NULL CHECK (term IN (1, 2, 3)),
                    chapter_number INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    textbook_pages TEXT,
                    lesson_id TEXT,
                    UNIQUE (subject_id, term, chapter_number)
                );
                CREATE TABLE IF NOT EXISTS curriculum_concepts (
                    id TEXT PRIMARY KEY,
                    chapter_id TEXT NOT NULL REFERENCES curriculum_chapters(id),
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    key_points_json TEXT NOT NULL,
                    display_order INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS students (
                    id TEXT PRIMARY KEY,
                    nickname TEXT NOT NULL UNIQUE,
                    pin_hash TEXT NOT NULL,
                    board TEXT NOT NULL DEFAULT 'TN_STATE_BOARD',
                    class_level INTEGER NOT NULL DEFAULT 6,
                    grade_band TEXT NOT NULL DEFAULT '6-7',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS learner_active_position (
                    learner_id TEXT NOT NULL,
                    subject_id TEXT NOT NULL,
                    chapter_id TEXT NOT NULL,
                    concept_id TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (learner_id, subject_id)
                );
                """
            )
            self._ensure_learner_columns(connection)
            self._ensure_question_columns(connection)
            connection.executemany(
                """
                INSERT OR IGNORE INTO curriculum_subjects
                    (id, name, code, icon, accent_color, display_order)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        sub["id"],
                        sub["name"],
                        sub["code"],
                        sub["icon"],
                        sub["accent_color"],
                        sub["display_order"],
                    )
                    for sub in CURRICULUM_SUBJECTS
                ],
            )
            connection.executemany(
                """
                INSERT OR IGNORE INTO curriculum_chapters
                    (id, subject_id, term, chapter_number, title, description, textbook_pages, lesson_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        ch["id"],
                        ch["subject_id"],
                        ch["term"],
                        ch["chapter_number"],
                        ch["title"],
                        ch["description"],
                        ch["textbook_pages"],
                        ch["lesson_id"],
                    )
                    for ch in CURRICULUM_CHAPTERS
                ],
            )
            connection.executemany(
                """
                INSERT OR IGNORE INTO curriculum_concepts
                    (id, chapter_id, title, summary, key_points_json, display_order)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        co["id"],
                        co["chapter_id"],
                        co["title"],
                        co["summary"],
                        json.dumps(co["key_points"]),
                        co["display_order"],
                    )
                    for co in CURRICULUM_CONCEPTS
                ],
            )
            connection.executemany(
                """
                INSERT OR IGNORE INTO lessons
                    (id, subject_id, subject_name, topic, title, content_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        lesson["id"],
                        lesson["subject_id"],
                        lesson["subject_name"],
                        lesson["topic"],
                        lesson["title"],
                        json.dumps(lesson["content"]),
                    )
                    for lesson in ALL_LESSONS
                ],
            )
            connection.executemany(
                """
                INSERT OR IGNORE INTO questions
                    (id, lesson_id, subject_id, topic, difficulty, rating, prompt, choices_json, accepted_answers_json, hint, explanation, concept_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        question["id"],
                        question["lesson_id"],
                        question["subject_id"],
                        question["topic"],
                        question["difficulty"],
                        question["rating"],
                        question["prompt"],
                        json.dumps(question["choices"]),
                        json.dumps(question["accepted_answers"]),
                        question.get("hint"),
                        question.get("explanation"),
                        question.get("concept_id"),
                    )
                    for question in ALL_QUESTIONS
                ],
            )

    @staticmethod
    def _ensure_learner_columns(connection: sqlite3.Connection) -> None:
        """Add quiz fields when opening a database made by the previous prototype."""
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(learners)")}
        required_columns = {
            "ability": "REAL NOT NULL DEFAULT 1000",
            "points": "INTEGER NOT NULL DEFAULT 0",
            "correct_streak": "INTEGER NOT NULL DEFAULT 0",
            "incorrect_streak": "INTEGER NOT NULL DEFAULT 0",
            "target_difficulty": "TEXT NOT NULL DEFAULT 'medium'",
        }
        for name, definition in required_columns.items():
            if name not in columns:
                connection.execute(f"ALTER TABLE learners ADD COLUMN {name} {definition}")

    @staticmethod
    def _ensure_question_columns(connection: sqlite3.Connection) -> None:
        """Add hint, explanation, and concept_id fields to questions table if missing."""
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(questions)")}
        if "hint" not in columns:
            connection.execute("ALTER TABLE questions ADD COLUMN hint TEXT")
        if "explanation" not in columns:
            connection.execute("ALTER TABLE questions ADD COLUMN explanation TEXT")
        if "concept_id" not in columns:
            connection.execute("ALTER TABLE questions ADD COLUMN concept_id TEXT")

    def create_learner(self, learner_id: str, nickname: str, grade_band: str, created_at: str) -> dict[str, str]:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO learners (id, nickname, grade_band, created_at) VALUES (?, ?, ?, ?)",
                (learner_id, nickname, grade_band, created_at),
            )
        return {"id": learner_id, "nickname": nickname, "grade_band": grade_band}

    def get_learner(self, learner_id: str) -> dict[str, str] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT id, nickname, grade_band FROM learners WHERE id = ?", (learner_id,)
            ).fetchone()
        return dict(row) if row else None

    def create_student(
        self,
        student_id: str,
        nickname: str,
        pin_hash: str,
        created_at: str,
        board: str = "TN_STATE_BOARD",
        class_level: int = 6,
        grade_band: str = "6-7",
    ) -> dict[str, object]:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO students (id, nickname, pin_hash, board, class_level, grade_band, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (student_id, nickname, pin_hash, board, class_level, grade_band, created_at),
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO learners (id, nickname, grade_band, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (student_id, nickname, grade_band, created_at),
            )
        return {
            "id": student_id,
            "nickname": nickname,
            "board": board,
            "class_level": class_level,
            "grade_band": grade_band,
            "created_at": created_at,
        }

    def get_student_by_nickname(self, nickname: str) -> dict[str, object] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT id, nickname, pin_hash, board, class_level, grade_band, created_at
                FROM students
                WHERE LOWER(nickname) = LOWER(?)
                """,
                (nickname.strip(),),
            ).fetchone()
        return dict(row) if row else None

    def get_student_by_id(self, student_id: str) -> dict[str, object] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT id, nickname, pin_hash, board, class_level, grade_band, created_at
                FROM students
                WHERE id = ?
                """,
                (student_id,),
            ).fetchone()
        return dict(row) if row else None

    def list_subjects(self) -> list[dict[str, str]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT DISTINCT subject_id, subject_name FROM lessons ORDER BY subject_id"
            ).fetchall()
        return [{"id": row["subject_id"], "name": row["subject_name"], "language": "English"} for row in rows]

    def list_curriculum_subjects(self) -> list[dict[str, object]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT s.id, s.name, s.code, s.icon, s.accent_color, s.display_order,
                       COUNT(DISTINCT c.id) as chapter_count
                FROM curriculum_subjects s
                LEFT JOIN curriculum_chapters c ON c.subject_id = s.id
                GROUP BY s.id
                ORDER BY s.display_order ASC
                """
            ).fetchall()
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "code": row["code"],
                "icon": row["icon"],
                "accent_color": row["accent_color"],
                "display_order": row["display_order"],
                "chapter_count": row["chapter_count"],
                "terms_available": [1],
            }
            for row in rows
        ]

    def get_curriculum_subject(self, subject_id: str) -> dict[str, object] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT id, name, code, icon, accent_color, display_order
                FROM curriculum_subjects
                WHERE id = ?
                """,
                (subject_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "code": row["code"],
            "icon": row["icon"],
            "accent_color": row["accent_color"],
            "display_order": row["display_order"],
        }

    def get_chapters_by_term(self, subject_id: str, term: int) -> list[dict[str, object]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT c.id, c.subject_id, c.term, c.chapter_number, c.title, c.description,
                       c.textbook_pages, c.lesson_id,
                       COUNT(co.id) as concept_count
                FROM curriculum_chapters c
                LEFT JOIN curriculum_concepts co ON co.chapter_id = c.id
                WHERE c.subject_id = ? AND c.term = ?
                GROUP BY c.id
                ORDER BY c.chapter_number ASC
                """,
                (subject_id, term),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "subject_id": row["subject_id"],
                "term": row["term"],
                "chapter_number": row["chapter_number"],
                "title": row["title"],
                "description": row["description"],
                "textbook_pages": row["textbook_pages"],
                "lesson_id": row["lesson_id"],
                "concept_count": row["concept_count"],
            }
            for row in rows
        ]

    def get_chapter(self, chapter_id: str) -> dict[str, object] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT id, subject_id, term, chapter_number, title, description, textbook_pages, lesson_id
                FROM curriculum_chapters
                WHERE id = ?
                """,
                (chapter_id,),
            ).fetchone()
            if not row:
                return None
            concepts = connection.execute(
                """
                SELECT id, chapter_id, title, summary, key_points_json, display_order
                FROM curriculum_concepts
                WHERE chapter_id = ?
                ORDER BY display_order ASC
                """,
                (chapter_id,),
            ).fetchall()
        return {
            "id": row["id"],
            "subject_id": row["subject_id"],
            "term": row["term"],
            "chapter_number": row["chapter_number"],
            "title": row["title"],
            "description": row["description"],
            "textbook_pages": row["textbook_pages"],
            "lesson_id": row["lesson_id"],
            "concepts": [
                {
                    "id": c["id"],
                    "chapter_id": c["chapter_id"],
                    "title": c["title"],
                    "summary": c["summary"],
                    "key_points": json.loads(c["key_points_json"]),
                    "display_order": c["display_order"],
                }
                for c in concepts
            ],
        }

    def get_chapter_by_unit(
        self, subject_id: str, chapter_number: int, term: int = 1
    ) -> dict[str, object] | None:
        """Find a curriculum chapter by subject and unit/chapter number."""
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT id FROM curriculum_chapters
                WHERE subject_id = ? AND chapter_number = ? AND term = ?
                """,
                (subject_id, chapter_number, term),
            ).fetchone()
            if not row:
                return None
            chapter_id = row["id"]
        return self.get_chapter(chapter_id)

    def find_chapter_by_title(
        self, title_query: str, subject_id: str | None = None
    ) -> dict[str, object] | None:
        """Find the best matching curriculum chapter by title or topic keywords."""
        cleaned = title_query.strip().lower()
        query = """
            SELECT id FROM curriculum_chapters
            WHERE lower(title) LIKE ?
        """
        params: list[Any] = [f"%{cleaned}%"]
        if subject_id:
            query += " AND subject_id = ?"
            params.append(subject_id)
        query += " LIMIT 1"

        with self.connection() as connection:
            row = connection.execute(query, params).fetchone()
            if not row:
                return None
            chapter_id = row["id"]
        return self.get_chapter(chapter_id)

    def get_concept(self, concept_id: str) -> dict[str, object] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT id, chapter_id, title, summary, key_points_json, display_order
                FROM curriculum_concepts
                WHERE id = ?
                """,
                (concept_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "chapter_id": row["chapter_id"],
            "title": row["title"],
            "summary": row["summary"],
            "key_points": json.loads(row["key_points_json"]),
            "display_order": row["display_order"],
        }

    def get_concept_lesson(self, concept_id: str) -> dict[str, object] | None:
        """Return a concept with chapter metadata and prev/next sibling navigation."""
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT co.id, co.chapter_id, co.title, co.summary,
                       co.key_points_json, co.display_order,
                       ch.title AS chapter_title, ch.description AS chapter_description,
                       ch.textbook_pages, ch.term, ch.chapter_number,
                       s.id AS subject_id, s.name AS subject_name, s.icon AS subject_icon,
                       s.accent_color AS subject_accent
                FROM curriculum_concepts co
                JOIN curriculum_chapters ch ON ch.id = co.chapter_id
                JOIN curriculum_subjects s ON s.id = ch.subject_id
                WHERE co.id = ?
                """,
                (concept_id,),
            ).fetchone()
            if not row:
                return None
            # Fetch all sibling concepts ordered by display_order
            siblings = connection.execute(
                """
                SELECT id, title, display_order
                FROM curriculum_concepts
                WHERE chapter_id = ?
                ORDER BY display_order ASC
                """,
                (row["chapter_id"],),
            ).fetchall()

        siblings_list = [dict(s) for s in siblings]
        current_index = next(
            (i for i, s in enumerate(siblings_list) if s["id"] == concept_id), 0
        )
        prev_concept = siblings_list[current_index - 1] if current_index > 0 else None
        next_concept = (
            siblings_list[current_index + 1]
            if current_index < len(siblings_list) - 1
            else None
        )

        key_points = json.loads(row["key_points_json"])
        return {
            "id": row["id"],
            "chapter_id": row["chapter_id"],
            "title": row["title"],
            "summary": row["summary"],
            "key_points": key_points,
            "display_order": row["display_order"],
            "index": current_index,
            "total": len(siblings_list),
            "chapter_title": row["chapter_title"],
            "chapter_description": row["chapter_description"],
            "textbook_pages": row["textbook_pages"],
            "term": row["term"],
            "chapter_number": row["chapter_number"],
            "subject_id": row["subject_id"],
            "subject_name": row["subject_name"],
            "subject_icon": row["subject_icon"],
            "subject_accent": row["subject_accent"],
            "prev_concept": prev_concept,
            "next_concept": next_concept,
            "all_concepts": [
                {"id": s["id"], "title": s["title"], "display_order": s["display_order"]}
                for s in siblings_list
            ],
        }

    def get_lesson(self, lesson_id: str) -> dict[str, object] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT id, subject_name, topic, title, content_json FROM lessons WHERE id = ?", (lesson_id,)
            ).fetchone()
            if row:
                return {
                    "id": row["id"],
                    "subject": row["subject_name"],
                    "topic": row["topic"],
                    "title": row["title"],
                    "content": json.loads(row["content_json"]),
                }

            # Fallback: check if lesson_id is a curriculum concept ID
            concept_row = connection.execute(
                """
                SELECT c.id, c.title, c.summary, c.key_points_json,
                       ch.title AS chapter_title, s.name AS subject_name
                FROM curriculum_concepts c
                JOIN curriculum_chapters ch ON c.chapter_id = ch.id
                JOIN curriculum_subjects s ON ch.subject_id = s.id
                WHERE c.id = ?
                """,
                (lesson_id,),
            ).fetchone()
            if concept_row:
                key_points = []
                if concept_row["key_points_json"]:
                    try:
                        key_points = json.loads(concept_row["key_points_json"])
                    except Exception:
                        key_points = []
                return {
                    "id": concept_row["id"],
                    "subject": concept_row["subject_name"],
                    "topic": concept_row["chapter_title"],
                    "title": concept_row["title"],
                    "content": {
                        "summary": concept_row["summary"] or "",
                        "key_points": key_points,
                    },
                }
        return None

    def get_next_question(
        self,
        learner_id: str,
        subject_id: str,
        concept_id: str | None = None,
        chapter_id: str | None = None,
    ) -> dict[str, object] | None:
        """Select an unanswered question in the learner's target band when possible."""
        with self.connection() as connection:
            learner = connection.execute(
                "SELECT ability, target_difficulty FROM learners WHERE id = ?", (learner_id,)
            ).fetchone()
            if not learner:
                return None

            rows = []
            # If concept_id is provided, try to find questions specifically for this concept
            if concept_id:
                rows = connection.execute(
                    """
                    SELECT q.id, q.lesson_id, q.topic, q.difficulty, q.rating, q.prompt, q.choices_json, q.hint
                    FROM questions q
                    WHERE (q.concept_id = ? OR q.lesson_id = ?)
                      AND NOT EXISTS (
                          SELECT 1 FROM attempts a
                          WHERE a.learner_id = ? AND a.question_id = q.id
                      )
                    """,
                    (concept_id, concept_id, learner_id),
                ).fetchall()

            # If no rows found and chapter_id is provided, look for chapter questions
            if not rows and chapter_id:
                rows = connection.execute(
                    """
                    SELECT q.id, q.lesson_id, q.topic, q.difficulty, q.rating, q.prompt, q.choices_json, q.hint
                    FROM questions q
                    WHERE (q.lesson_id LIKE ? OR q.topic LIKE ?)
                      AND NOT EXISTS (
                          SELECT 1 FROM attempts a
                          WHERE a.learner_id = ? AND a.question_id = q.id
                      )
                    """,
                    (f"%{chapter_id}%", f"%{chapter_id}%", learner_id),
                ).fetchall()

            # Fall back to subject-wide questions
            if not rows:
                rows = connection.execute(
                    """
                    SELECT q.id, q.lesson_id, q.topic, q.difficulty, q.rating, q.prompt, q.choices_json, q.hint
                    FROM questions q
                    WHERE q.subject_id = ?
                      AND NOT EXISTS (
                          SELECT 1 FROM attempts a
                          WHERE a.learner_id = ? AND a.question_id = q.id
                      )
                    """,
                    (subject_id, learner_id),
                ).fetchall()

        if not rows:
            return None

        target_rows = [row for row in rows if row["difficulty"] == learner["target_difficulty"]]
        candidates = target_rows or rows
        question = min(candidates, key=lambda row: abs(row["rating"] - learner["ability"]))
        return {
            "id": question["id"],
            "lesson_id": question["lesson_id"],
            "topic": question["topic"],
            "difficulty": question["difficulty"],
            "prompt": question["prompt"],
            "choices": json.loads(question["choices_json"]),
            "hint": question["hint"] if "hint" in question.keys() else None,
        }

    def subject_has_questions(self, subject_id: str) -> bool:
        with self.connection() as connection:
            return connection.execute(
                "SELECT EXISTS(SELECT 1 FROM questions WHERE subject_id = ?)", (subject_id,)
            ).fetchone()[0] == 1

    def subject_exists(self, subject_id: str) -> bool:
        with self.connection() as connection:
            return connection.execute(
                "SELECT EXISTS(SELECT 1 FROM lessons WHERE subject_id = ?)", (subject_id,)
            ).fetchone()[0] == 1

    def question_exists(self, question_id: str) -> bool:
        with self.connection() as connection:
            return connection.execute(
                "SELECT EXISTS(SELECT 1 FROM questions WHERE id = ?)", (question_id,)
            ).fetchone()[0] == 1

    def submit_answer(
        self, learner_id: str, question_id: str, submitted_answer: str, attempt_id: str, created_at: str
    ) -> dict[str, object] | None:
        """Store one answer atomically and return feedback without exposing answer keys."""
        with self.connection() as connection:
            learner = connection.execute("SELECT * FROM learners WHERE id = ?", (learner_id,)).fetchone()
            question = connection.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
            if not learner or not question:
                return None

            accepted_answers_raw = json.loads(question["accepted_answers_json"])
            accepted_answers = {_normalise_answer(answer) for answer in accepted_answers_raw}
            is_correct = _normalise_answer(submitted_answer) in accepted_answers
            primary_answer = accepted_answers_raw[0] if accepted_answers_raw else ""
            explanation = (
                question["explanation"]
                if ("explanation" in question.keys() and question["explanation"])
                else f"The correct answer is '{primary_answer}'. Review {question['topic']} to reinforce this concept!"
            )

            existing_attempt = connection.execute(
                "SELECT is_correct, points_awarded FROM attempts WHERE learner_id = ? AND question_id = ?",
                (learner_id, question_id),
            ).fetchone()
            if existing_attempt:
                return {
                    "correct": bool(existing_attempt["is_correct"]),
                    "points_awarded": 0,
                    "ability": round(learner["ability"], 2),
                    "target_difficulty": learner["target_difficulty"],
                    "duplicate_submission": True,
                    "explanation": explanation,
                    "correct_answer": primary_answer,
                }

            expected_score = 1 / (1 + math.pow(10, (question["rating"] - learner["ability"]) / 400))
            new_ability = learner["ability"] + 32 * ((1 if is_correct else 0) - expected_score)
            correct_streak = learner["correct_streak"] + 1 if is_correct else 0
            incorrect_streak = learner["incorrect_streak"] + 1 if not is_correct else 0
            target_difficulty = learner["target_difficulty"]
            if correct_streak >= 2:
                target_difficulty = _raise_difficulty(target_difficulty)
            elif incorrect_streak >= 2:
                target_difficulty = _lower_difficulty(target_difficulty)
            points_awarded = 15 if is_correct else 0

            connection.execute(
                """
                INSERT INTO attempts
                    (id, learner_id, question_id, submitted_answer, is_correct, points_awarded, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (attempt_id, learner_id, question_id, submitted_answer, is_correct, points_awarded, created_at),
            )
            connection.execute(
                """
                UPDATE learners
                SET ability = ?, points = points + ?, correct_streak = ?, incorrect_streak = ?, target_difficulty = ?
                WHERE id = ?
                """,
                (new_ability, points_awarded, correct_streak, incorrect_streak, target_difficulty, learner_id),
            )
            _update_progress(connection, "learner_topic_progress", learner_id, question["topic"], is_correct)
            _update_progress(connection, "learner_lesson_progress", learner_id, question["lesson_id"], is_correct)
        return {
            "correct": is_correct,
            "points_awarded": points_awarded,
            "ability": round(new_ability, 2),
            "target_difficulty": target_difficulty,
            "duplicate_submission": False,
            "explanation": explanation,
            "correct_answer": primary_answer,
        }

    def get_progress(self, learner_id: str) -> dict[str, object] | None:
        with self.connection() as connection:
            learner = connection.execute(
                """
                SELECT id, ability, points, correct_streak, incorrect_streak, target_difficulty
                FROM learners WHERE id = ?
                """,
                (learner_id,),
            ).fetchone()
            if not learner:
                return None
            topics = connection.execute(
                """
                SELECT topic, attempts_count, correct_count
                FROM learner_topic_progress WHERE learner_id = ? ORDER BY topic
                """,
                (learner_id,),
            ).fetchall()
            lessons = connection.execute(
                """
                SELECT lesson_id, attempts_count, correct_count
                FROM learner_lesson_progress WHERE learner_id = ? ORDER BY lesson_id
                """,
                (learner_id,),
            ).fetchall()
        return {
            "learner_id": learner["id"],
            "ability": round(learner["ability"], 2),
            "points": learner["points"],
            "correct_streak": learner["correct_streak"],
            "incorrect_streak": learner["incorrect_streak"],
            "target_difficulty": learner["target_difficulty"],
            "topics": [_progress_row(row, "topic") for row in topics],
            "lessons": [_progress_row(row, "lesson_id") for row in lessons],
        }

    def save_active_position(
        self, learner_id: str, subject_id: str, chapter_id: str, concept_id: str, updated_at: str | None = None
    ) -> dict[str, str]:
        """Persist the learner's last visited curriculum position."""
        from datetime import datetime, timezone
        ts = updated_at or datetime.now(timezone.utc).isoformat()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO learner_active_position (learner_id, subject_id, chapter_id, concept_id, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (learner_id, subject_id) DO UPDATE SET
                    chapter_id = excluded.chapter_id,
                    concept_id = excluded.concept_id,
                    updated_at = excluded.updated_at
                """,
                (learner_id, subject_id, chapter_id, concept_id, ts),
            )
        return {
            "learner_id": learner_id,
            "subject_id": subject_id,
            "chapter_id": chapter_id,
            "concept_id": concept_id,
            "updated_at": ts,
        }

    def get_active_position(self, learner_id: str, subject_id: str | None = None) -> dict[str, object] | None:
        """Retrieve the learner's last visited position for a subject or overall."""
        with self.connection() as connection:
            if subject_id:
                row = connection.execute(
                    """
                    SELECT p.learner_id, p.subject_id, p.chapter_id, p.concept_id, p.updated_at,
                           ch.title as chapter_title, ch.chapter_number,
                           cp.title as concept_title, cp.summary as concept_summary,
                           s.name as subject_name
                    FROM learner_active_position p
                    JOIN curriculum_chapters ch ON p.chapter_id = ch.id
                    JOIN curriculum_concepts cp ON p.concept_id = cp.id
                    JOIN curriculum_subjects s ON p.subject_id = s.id
                    WHERE p.learner_id = ? AND p.subject_id = ?
                    """,
                    (learner_id, subject_id),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT p.learner_id, p.subject_id, p.chapter_id, p.concept_id, p.updated_at,
                           ch.title as chapter_title, ch.chapter_number,
                           cp.title as concept_title, cp.summary as concept_summary,
                           s.name as subject_name
                    FROM learner_active_position p
                    JOIN curriculum_chapters ch ON p.chapter_id = ch.id
                    JOIN curriculum_concepts cp ON p.concept_id = cp.id
                    JOIN curriculum_subjects s ON p.subject_id = s.id
                    WHERE p.learner_id = ?
                    ORDER BY p.updated_at DESC LIMIT 1
                    """,
                    (learner_id,),
                ).fetchone()
        if not row:
            return None
        return dict(row)


def _normalise_answer(answer: str) -> str:
    return " ".join(answer.casefold().split())


def _raise_difficulty(difficulty: str) -> str:
    return {"easy": "medium", "medium": "hard", "hard": "hard"}[difficulty]


def _lower_difficulty(difficulty: str) -> str:
    return {"easy": "easy", "medium": "easy", "hard": "medium"}[difficulty]


def _update_progress(
    connection: sqlite3.Connection, table_name: str, learner_id: str, dimension: str, is_correct: bool
) -> None:
    dimension_column = "topic" if table_name == "learner_topic_progress" else "lesson_id"
    connection.execute(
        f"""
        INSERT INTO {table_name} (learner_id, {dimension_column}, attempts_count, correct_count)
        VALUES (?, ?, 1, ?)
        ON CONFLICT (learner_id, {dimension_column}) DO UPDATE SET
            attempts_count = attempts_count + 1,
            correct_count = correct_count + excluded.correct_count
        """,
        (learner_id, dimension, int(is_correct)),
    )


def _progress_row(row: sqlite3.Row, identifier: str) -> dict[str, object]:
    attempts = row["attempts_count"]
    return {
        identifier: row[identifier],
        "attempts": attempts,
        "correct_answers": row["correct_count"],
        "mastery_percent": round((row["correct_count"] / attempts) * 100, 1) if attempts else 0.0,
    }


def initialize_database(database_path: Path) -> None:
    """Create the SQLite schema and seed bundled lessons if they are absent."""
    Database(database_path).initialize()
