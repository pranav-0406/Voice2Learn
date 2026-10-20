"""Curriculum retrieval engine with transparent relevance scoring and context grounding.

Operates over SQLite curriculum tables:
- curriculum_concepts (title, summary, key_points_json)
- curriculum_chapters (title, description, subject_id)
- curriculum_subjects (id, name)
- lessons (topic, title, content_json)

Implements multi-factor ranking, active-lesson context boosts, and strict minimum
relevance thresholds to reject unsupported or random keyword hits.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from typing import Any

from app.db.database import Database

# Standard English stop words to exclude from query term analysis
STOP_WORDS: frozenset[str] = frozenset({
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "explain", "few", "for", "from", "further", "had", "hadn't",
    "has", "hasn't", "have", "haven't", "having", "he", "her", "here", "hers",
    "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is",
    "isn't", "it", "it's", "its", "itself", "just", "know", "let", "like", "me",
    "more", "most", "must", "my", "myself", "no", "nor", "not", "of", "off", "on",
    "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
    "over", "own", "same", "say", "saying", "she", "should", "shouldn't", "so",
    "some", "such", "tell", "than", "that", "that's", "the", "their", "theirs",
    "them", "themselves", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we",
    "were", "weren't", "what", "what's", "when", "where", "which", "while", "who",
    "whom", "why", "will", "with", "won't", "would", "wouldn't", "you", "your",
    "yours", "yourself", "yourselves",
})

# Minimum relevance score required to consider a query supported by the curriculum
MIN_RELEVANCE_THRESHOLD = 3.5

# Minimum ratio of substantive query terms that must appear in the candidate document
MIN_TERM_COVERAGE = 0.35


@dataclass(frozen=True)
class RetrievedCurriculumDoc:
    """A scored curriculum evidence unit for grounding RAG responses."""
    subject_id: str
    subject_name: str
    chapter_id: str
    chapter_title: str
    concept_id: str | None
    concept_title: str | None
    summary: str
    key_points: list[str] = field(default_factory=list)
    vocabulary: dict[str, str] = field(default_factory=dict)
    score: float = 0.0
    matched_terms: list[str] = field(default_factory=list)
    is_supported: bool = True

    @property
    def formatted_evidence(self) -> str:
        """Compact text representation for LLM prompt context."""
        parts = [
            f"Subject: {self.subject_name}",
            f"Chapter: {self.chapter_title}",
        ]
        if self.concept_title:
            parts.append(f"Concept: {self.concept_title}")
        parts.append(f"Summary: {self.summary}")
        if self.key_points:
            parts.append("Key Points: " + " | ".join(self.key_points[:4]))
        return "\n".join(parts)


def tokenize_query(query: str) -> list[str]:
    """Extract substantive, lowercased query terms excluding stop words."""
    cleaned = re.sub(r"[^\w\s-]", " ", query.lower())
    tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 1]
    substantive = [t for t in tokens if t not in STOP_WORDS]
    # Fallback to all tokens if every word was filtered as a stop word
    return substantive if substantive else tokens


class CurriculumRetriever:
    """Searches and scores SQLite curriculum concepts and lessons with multi-factor ranking."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def retrieve(
        self,
        query: str,
        context: dict[str, Any] | None = None,
        subject_id: str | None = None,
        chapter_id: str | None = None,
        concept_id: str | None = None,
        limit: int = 3,
    ) -> list[RetrievedCurriculumDoc]:
        """Retrieve top curriculum evidence items ranked by relevance and contextual proximity."""
        ctx = context or {}
        substantive_tokens = tokenize_query(query)
        if not substantive_tokens:
            return []

        # Context-derived filters
        active_subject = subject_id or ctx.get("subject_id")
        active_chapter = chapter_id or ctx.get("chapter_id")
        active_concept = concept_id or ctx.get("concept_id")

        # Infer subject filter if explicitly mentioned in query
        q_lower = query.lower()
        if not active_subject:
            if "science" in q_lower:
                active_subject = "science"
            elif "math" in q_lower or "mathematics" in q_lower:
                active_subject = "mathematics"
            elif "english" in q_lower:
                active_subject = "english"
            elif "social" in q_lower or "history" in q_lower or "geography" in q_lower:
                active_subject = "social_science"

        candidates = self._load_candidate_docs(active_subject)
        scored_docs: list[RetrievedCurriculumDoc] = []

        query_phrase = " ".join(substantive_tokens)

        for doc in candidates:
            score, matched_terms, coverage = self._score_doc(
                doc=doc,
                tokens=substantive_tokens,
                query_phrase=query_phrase,
                active_concept=active_concept,
                active_chapter=active_chapter,
                active_subject=active_subject,
                screen=str(ctx.get("screen", "")),
            )

            # Strict relevance check: requires both minimum total score AND term coverage
            # to avoid false positives on incidental single-word hits
            is_supported = (score >= MIN_RELEVANCE_THRESHOLD) and (coverage >= MIN_TERM_COVERAGE)

            if score > 0:
                scored_docs.append(
                    RetrievedCurriculumDoc(
                        subject_id=doc.subject_id,
                        subject_name=doc.subject_name,
                        chapter_id=doc.chapter_id,
                        chapter_title=doc.chapter_title,
                        concept_id=doc.concept_id,
                        concept_title=doc.concept_title,
                        summary=doc.summary,
                        key_points=doc.key_points,
                        vocabulary=doc.vocabulary,
                        score=score,
                        matched_terms=matched_terms,
                        is_supported=is_supported,
                    )
                )

        scored_docs.sort(key=lambda d: d.score, reverse=True)
        return scored_docs[:limit]

    def _score_doc(
        self,
        doc: RetrievedCurriculumDoc,
        tokens: list[str],
        query_phrase: str,
        active_concept: str | None,
        active_chapter: str | None,
        active_subject: str | None,
        screen: str,
    ) -> tuple[float, list[str], float]:
        """Compute transparent multi-factor relevance score."""
        score = 0.0
        matched_terms: list[str] = []

        title_text = f"{doc.concept_title or ''} {doc.chapter_title}".lower()
        body_text = f"{doc.summary} {' '.join(doc.key_points)}".lower()

        # 1. Exact phrase matches (highest confidence)
        if query_phrase and len(tokens) > 1:
            if query_phrase in title_text:
                score += 12.0
            elif query_phrase in body_text:
                score += 7.0

        # 2. Token overlap & keyword density
        matched_in_title = 0
        matched_in_body = 0
        for token in tokens:
            in_title = token in title_text
            in_body = token in body_text
            if in_title or in_body:
                matched_terms.append(token)
            if in_title:
                matched_in_title += 1
                score += 3.0
            if in_body:
                matched_in_body += 1
                score += 1.5

        coverage = len(matched_terms) / len(tokens) if tokens else 0.0
        score += coverage * 4.0

        # 3. All tokens present bonus
        if len(matched_terms) == len(tokens) and len(tokens) > 1:
            score += 3.0

        # 4. Contextual proximity boosts
        if active_concept and doc.concept_id == active_concept:
            score += 4.0
        elif active_chapter and doc.chapter_id == active_chapter:
            score += 2.5
        elif active_subject and doc.subject_id == active_subject:
            score += 1.0

        # Proximity from active screen path
        if doc.concept_id and doc.concept_id in screen:
            score += 3.0
        elif doc.chapter_id and doc.chapter_id in screen:
            score += 2.0

        return round(score, 2), matched_terms, coverage

    def _load_candidate_docs(self, subject_filter: str | None = None) -> list[RetrievedCurriculumDoc]:
        """Load curriculum concepts and chapter lessons from SQLite."""
        docs: list[RetrievedCurriculumDoc] = []
        with self.database.connection() as connection:
            # 1. Load concepts
            query = """
                SELECT
                    s.id as subject_id,
                    s.name as subject_name,
                    ch.id as chapter_id,
                    ch.title as chapter_title,
                    cp.id as concept_id,
                    cp.title as concept_title,
                    cp.summary as summary,
                    cp.key_points_json as key_points_json
                FROM curriculum_concepts cp
                JOIN curriculum_chapters ch ON cp.chapter_id = ch.id
                JOIN curriculum_subjects s ON ch.subject_id = s.id
            """
            params: list[Any] = []
            if subject_filter:
                query += " WHERE s.id = ?"
                params.append(subject_filter)

            rows = connection.execute(query, params).fetchall()
            for r in rows:
                try:
                    kps = json.loads(r["key_points_json"]) if r["key_points_json"] else []
                except Exception:
                    kps = []
                docs.append(
                    RetrievedCurriculumDoc(
                        subject_id=r["subject_id"],
                        subject_name=r["subject_name"],
                        chapter_id=r["chapter_id"],
                        chapter_title=r["chapter_title"],
                        concept_id=r["concept_id"],
                        concept_title=r["concept_title"],
                        summary=r["summary"],
                        key_points=kps,
                    )
                )

            # 2. Also load lessons that might contain extra vocabulary or facts
            lesson_query = """
                SELECT
                    l.id as lesson_id,
                    l.subject_id,
                    l.subject_name,
                    l.topic,
                    l.title,
                    l.content_json,
                    ch.id as chapter_id,
                    ch.title as chapter_title
                FROM lessons l
                LEFT JOIN curriculum_chapters ch ON ch.lesson_id = l.id
            """
            l_params: list[Any] = []
            if subject_filter:
                lesson_query += " WHERE l.subject_id = ?"
                l_params.append(subject_filter)

            l_rows = connection.execute(lesson_query, l_params).fetchall()
            for lr in l_rows:
                try:
                    content = json.loads(lr["content_json"]) if lr["content_json"] else {}
                except Exception:
                    content = {}
                summary = content.get("summary") or lr["title"]
                key_points = content.get("key_points") or []
                vocab = content.get("vocabulary") or {}
                ch_id = lr["chapter_id"] or lr["lesson_id"]
                ch_title = lr["chapter_title"] or lr["topic"]
                docs.append(
                    RetrievedCurriculumDoc(
                        subject_id=lr["subject_id"],
                        subject_name=lr["subject_name"],
                        chapter_id=ch_id,
                        chapter_title=ch_title,
                        concept_id=None,
                        concept_title=lr["title"],
                        summary=summary,
                        key_points=key_points,
                        vocabulary=vocab,
                    )
                )

        return docs
