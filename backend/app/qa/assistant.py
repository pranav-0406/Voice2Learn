"""Curriculum-grounded RAG Assistant for Tamil Nadu Class 6 students (English-only).

Generates educational voice responses strictly grounded in SQLite curriculum evidence.
If the language model is offline or unconfigured, falls back to direct stored curriculum
summaries and key points. Rejects out-of-scope questions honestly without hallucinations.
Never returns or executes voice commands.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from app.qa.groq import LanguageModelUnavailableError
from app.qa.ollama import OllamaUnavailableError
from app.qa.retriever import CurriculumRetriever, RetrievedCurriculumDoc, tokenize_query
from app.voice.understanding import LanguageModelProvider

logger = logging.getLogger(__name__)

OUT_OF_SCOPE_MESSAGE = (
    "That topic is outside our Class 6 curriculum. "
    "You can ask me about our Science, Mathematics, English, or Social Science lessons."
)

CLARIFICATION_PROMPT = (
    "Which lesson or topic are you asking about? "
    "Say the name of the topic, like 'States of Matter' or 'Sea Turtles'."
)


@dataclass(frozen=True)
class CurriculumSource:
    """Attribution metadata for the curriculum evidence used."""
    subject_id: str
    subject_name: str
    chapter_id: str
    chapter_title: str
    concept_id: str | None = None
    concept_title: str | None = None


@dataclass(frozen=True)
class CurriculumAnswer:
    """The final grounded answer and source metadata."""
    question: str
    answer: str
    supported: bool
    source: CurriculumSource | None = None
    clarification: str | None = None


# Anaphoric pronouns indicating a follow-up question requiring active screen context
ANAPHORIC_PATTERNS = [
    re.compile(r"\b(it|its|this|that|they|these|those)\b", re.IGNORECASE),
    re.compile(r"^(why|how|explain|tell me more|what about it)\b", re.IGNORECASE),
]


def is_anaphoric_follow_up(query: str) -> bool:
    """Detect if the student question is a follow-up referring to the current screen."""
    cleaned = re.sub(r"[^\w\s-]", " ", query.lower())
    words = [w.strip() for w in cleaned.split() if w.strip()]
    from app.qa.retriever import STOP_WORDS
    substantive = [w for w in words if w not in STOP_WORDS]
    has_pronoun = any(p.search(query) for p in ANAPHORIC_PATTERNS)
    # Follow-up if it has an anaphoric pronoun/opener and at most 2 substantive topic words
    return has_pronoun and len(substantive) <= 2


def resolve_follow_up_query(query: str, context: dict[str, Any]) -> str:
    """Enrich anaphoric follow-up queries using active screen/lesson context."""
    lesson_topic = context.get("lesson_topic")
    active_concept = context.get("concept_title")
    anchor = active_concept or lesson_topic
    if anchor:
        return f"{anchor} {query}"
    return query


def generate_direct_summary_answer(doc: RetrievedCurriculumDoc, query: str) -> str:
    """Extract a concise, direct answer sentence from the retrieved curriculum evidence.

    Used when LLM is unavailable (offline mode) or fails to respond.
    """
    tokens = set(tokenize_query(query))

    # 1. Check if any individual key point has high term overlap with the query
    best_kp: str | None = None
    best_overlap = 0
    for kp in doc.key_points:
        kp_tokens = set(tokenize_query(kp))
        overlap = len(tokens.intersection(kp_tokens))
        if overlap > best_overlap:
            best_overlap = overlap
            best_kp = kp

    if best_kp and best_overlap >= 2:
        return best_kp

    # 2. Otherwise return the concept/lesson summary
    summary = doc.summary.strip()
    if summary:
        # Keep only the first 1-2 sentences for concise voice playback
        sentences = re.split(r"(?<=[.!?])\s+", summary)
        return " ".join(sentences[:2]).strip()

    return f"{doc.concept_title or doc.chapter_title}: {doc.key_points[0] if doc.key_points else ''}".strip()


def build_grounded_prompt(query: str, evidence: list[RetrievedCurriculumDoc]) -> str:
    """Construct a strict prompt instructing the model to answer using only evidence."""
    evidence_text = "\n\n".join(
        f"--- Evidence {i+1} ---\n{doc.formatted_evidence}"
        for i, doc in enumerate(evidence)
    )

    return f"""You are Voice2Learn's Class 6 educational tutor for Tamil Nadu students.
Answer the student's question using ONLY the retrieved curriculum evidence below.

Rules:
1. Ground every statement strictly in the provided evidence. Do NOT invent facts.
2. Keep the answer under 35 words (1-2 sentences) so it is clear and easy to understand via voice.
3. If the evidence does NOT contain sufficient facts to answer the question, set supported to false and provide a brief clarification.
4. Do not use asterisks, markdown, bullet points, or formulas that sound awkward when read aloud.
5. Return JSON ONLY with keys:
   "supported": true or false,
   "response": "short spoken answer",
   "clarification": "clarification or null"

Question: {query}

Retrieved Evidence:
{evidence_text}"""


class CurriculumAssistant:
    """Coordinates retrieval, context resolution, and grounded answer synthesis."""

    def __init__(self, retriever: CurriculumRetriever) -> None:
        self.retriever = retriever

    def answer_question(
        self,
        query: str,
        context: dict[str, Any] | None = None,
        provider: LanguageModelProvider | None = None,
        subject_id: str | None = None,
        chapter_id: str | None = None,
        concept_id: str | None = None,
    ) -> CurriculumAnswer:
        """Answer a student's question grounded in Class 6 curriculum evidence."""
        ctx = context or {}
        cleaned_query = query.strip()
        if not cleaned_query:
            return CurriculumAnswer(
                question=query,
                answer="Please ask a question about your lessons.",
                supported=False,
                clarification=CLARIFICATION_PROMPT,
            )

        # 1. Resolve anaphoric follow-up queries if on an active lesson screen
        search_query = cleaned_query
        if is_anaphoric_follow_up(cleaned_query):
            has_context = bool(ctx.get("lesson_topic") or ctx.get("concept_title") or ctx.get("screen"))
            from app.qa.retriever import STOP_WORDS
            words = [w for w in re.sub(r"[^\w\s-]", " ", cleaned_query.lower()).split() if w.strip()]
            substantive = [w for w in words if w not in STOP_WORDS]
            if not has_context and len(substantive) == 0:
                # Vague question with no context at all (e.g. "What is it?")
                return CurriculumAnswer(
                    question=query,
                    answer=CLARIFICATION_PROMPT,
                    supported=False,
                    clarification=CLARIFICATION_PROMPT,
                )
            search_query = resolve_follow_up_query(cleaned_query, ctx)

        # 2. Retrieve curriculum evidence
        docs = self.retriever.retrieve(
            query=search_query,
            context=ctx,
            subject_id=subject_id,
            chapter_id=chapter_id,
            concept_id=concept_id,
            limit=2,
        )

        # 3. Check if top document satisfies relevance threshold
        if not docs or not docs[0].is_supported:
            logger.info("rag_unsupported_query query=%s top_score=%s", query, docs[0].score if docs else 0)
            return CurriculumAnswer(
                question=query,
                answer=OUT_OF_SCOPE_MESSAGE,
                supported=False,
                source=None,
                clarification=OUT_OF_SCOPE_MESSAGE,
            )

        top_doc = docs[0]
        source_meta = CurriculumSource(
            subject_id=top_doc.subject_id,
            subject_name=top_doc.subject_name,
            chapter_id=top_doc.chapter_id,
            chapter_title=top_doc.chapter_title,
            concept_id=top_doc.concept_id,
            concept_title=top_doc.concept_title,
        )

        # 4. If LLM provider is available, generate grounded natural answer
        if provider is not None and provider.configured:
            try:
                prompt = build_grounded_prompt(cleaned_query, docs)
                raw_response = provider.answer(prompt)
                parsed = self._parse_llm_response(raw_response)
                if parsed:
                    is_supp, response_text, clarif = parsed
                    if is_supp and response_text:
                        return CurriculumAnswer(
                            question=query,
                            answer=response_text,
                            supported=True,
                            source=source_meta,
                            clarification=clarif,
                        )
                    elif not is_supp:
                        return CurriculumAnswer(
                            question=query,
                            answer=response_text or OUT_OF_SCOPE_MESSAGE,
                            supported=False,
                            source=None,
                            clarification=clarif or OUT_OF_SCOPE_MESSAGE,
                        )
            except (LanguageModelUnavailableError, OllamaUnavailableError) as error:
                logger.warning("rag_provider_unavailable error=%s falling back to direct summary", error)
            except Exception as error:
                logger.exception("rag_llm_synthesis_failed falling back to direct summary")

        # 5. Offline / Graceful Fallback: direct summary from verified stored curriculum
        direct_answer = generate_direct_summary_answer(top_doc, cleaned_query)
        return CurriculumAnswer(
            question=query,
            answer=direct_answer,
            supported=True,
            source=source_meta,
            clarification=None,
        )

    def _parse_llm_response(self, raw: str) -> tuple[bool, str, str | None] | None:
        """Parse structured JSON response from the LLM."""
        text = raw.strip()
        if text.startswith("```") and text.endswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return None

        if not isinstance(data, dict):
            return None

        supported = bool(data.get("supported", True))
        response = data.get("response")
        clarification = data.get("clarification")

        response_str = str(response).strip() if response else ""
        clarif_str = str(clarification).strip() if clarification else None
        return supported, response_str, clarif_str
