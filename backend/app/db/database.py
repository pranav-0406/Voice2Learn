"""Small SQLite data access layer for learners and seeded lessons."""

from __future__ import annotations

import json
import math
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.db.seed import SCIENCE_LESSONS, SCIENCE_QUESTIONS


class Database:
    """Owns short-lived SQLite connections and the prototype's SQL queries."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

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
                    accepted_answers_json TEXT NOT NULL
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
                """
            )
            self._ensure_learner_columns(connection)
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
                    for lesson in SCIENCE_LESSONS
                ],
            )
            connection.executemany(
                """
                INSERT OR IGNORE INTO questions
                    (id, lesson_id, subject_id, topic, difficulty, rating, prompt, choices_json, accepted_answers_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    )
                    for question in SCIENCE_QUESTIONS
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

    def list_subjects(self) -> list[dict[str, str]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT DISTINCT subject_id, subject_name FROM lessons ORDER BY subject_id"
            ).fetchall()
        return [{"id": row["subject_id"], "name": row["subject_name"], "language": "English"} for row in rows]

    def get_lesson(self, lesson_id: str) -> dict[str, object] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT id, subject_name, topic, title, content_json FROM lessons WHERE id = ?", (lesson_id,)
            ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "subject": row["subject_name"],
            "topic": row["topic"],
            "title": row["title"],
            "content": json.loads(row["content_json"]),
        }

    def get_next_question(self, learner_id: str, subject_id: str) -> dict[str, object] | None:
        """Select an unanswered question in the learner's target band when possible."""
        with self.connection() as connection:
            learner = connection.execute(
                "SELECT ability, target_difficulty FROM learners WHERE id = ?", (learner_id,)
            ).fetchone()
            if not learner:
                return None
            rows = connection.execute(
                """
                SELECT q.id, q.lesson_id, q.topic, q.difficulty, q.rating, q.prompt, q.choices_json
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
                }

            accepted_answers = {_normalise_answer(answer) for answer in json.loads(question["accepted_answers_json"])}
            is_correct = _normalise_answer(submitted_answer) in accepted_answers
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
