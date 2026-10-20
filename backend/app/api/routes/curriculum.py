"""Dynamic curriculum endpoints for subjects, terms, chapters, and concepts."""

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.api.dependencies import get_curriculum_assistant, get_curriculum_resolver, get_database
from app.api.schemas import (
    ConceptLessonResponse,
    CurriculumAskRequest,
    CurriculumAskResponse,
    CurriculumChapterDetailResponse,
    CurriculumConceptResponse,
    CurriculumResolveRequest,
    CurriculumResolveResponse,
    CurriculumSourceMetadata,
    CurriculumSubjectResponse,
    CurriculumSubjectsResponse,
    CurriculumTermChaptersResponse,
)
from app.curriculum.resolver import CurriculumResolver
from app.db.database import Database
from app.qa.assistant import CurriculumAssistant
from app.voice.understanding import get_default_llm_provider

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


@router.get("/subjects", response_model=CurriculumSubjectsResponse)
def list_curriculum_subjects(
    database: Database = Depends(get_database),
) -> CurriculumSubjectsResponse:
    """List all official Class 6 curriculum subjects with chapter totals and terms."""
    subjects = database.list_curriculum_subjects()
    return CurriculumSubjectsResponse(subjects=subjects)


@router.get("/subjects/{subject_id}", response_model=CurriculumSubjectResponse)
def get_curriculum_subject(
    subject_id: str = Path(..., description="Subject identifier (e.g., 'science')"),
    database: Database = Depends(get_database),
) -> CurriculumSubjectResponse:
    """Get metadata for a single curriculum subject."""
    subject = database.get_curriculum_subject(subject_id)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject '{subject_id}' not found",
        )
    chapters = database.get_chapters_by_term(subject_id, 1)
    return CurriculumSubjectResponse(
        id=subject["id"],
        name=subject["name"],
        code=subject["code"],
        icon=subject["icon"],
        accent_color=subject["accent_color"],
        display_order=subject["display_order"],
        chapter_count=len(chapters),
        terms_available=[1],
    )


@router.get(
    "/subjects/{subject_id}/terms/{term}",
    response_model=CurriculumTermChaptersResponse,
)
def get_term_chapters(
    subject_id: str = Path(..., description="Subject identifier (e.g., 'mathematics')"),
    term: int = Path(..., ge=1, le=3, description="Academic term (1, 2, or 3)"),
    database: Database = Depends(get_database),
) -> CurriculumTermChaptersResponse:
    """List chapters for a specific subject and term."""
    subject = database.get_curriculum_subject(subject_id)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject '{subject_id}' not found",
        )
    chapters = database.get_chapters_by_term(subject_id, term)
    return CurriculumTermChaptersResponse(
        subject_id=subject_id,
        term=term,
        chapters=chapters,
    )


@router.get("/chapters/{chapter_id}", response_model=CurriculumChapterDetailResponse)
def get_chapter(
    chapter_id: str = Path(..., description="Chapter identifier (e.g., 'sci-term1-ch01')"),
    database: Database = Depends(get_database),
) -> CurriculumChapterDetailResponse:
    """Retrieve details and concept breakdown for a chapter."""
    chapter = database.get_chapter(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter '{chapter_id}' not found",
        )
    return CurriculumChapterDetailResponse(**chapter)


@router.get("/concepts/{concept_id}", response_model=CurriculumConceptResponse)
def get_concept(
    concept_id: str = Path(..., description="Concept identifier (e.g., 'sci-ch01-c01')"),
    database: Database = Depends(get_database),
) -> CurriculumConceptResponse:
    """Retrieve detailed learning points and summary for a single concept."""
    concept = database.get_concept(concept_id)
    if not concept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept '{concept_id}' not found",
        )
    return CurriculumConceptResponse(**concept)


@router.get("/concepts/{concept_id}/lesson", response_model=ConceptLessonResponse)
def get_concept_lesson(
    concept_id: str = Path(..., description="Concept identifier"),
    database: Database = Depends(get_database),
) -> ConceptLessonResponse:
    """Return a concept with full chapter/subject context and prev/next navigation.

    This is the primary endpoint used by the M04 ConceptViewer page. It returns
    everything needed to render a self-contained concept card with narration, prev/next
    navigation, and the complete table of contents for the parent chapter.
    """
    lesson = database.get_concept_lesson(concept_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept '{concept_id}' not found",
        )
    return ConceptLessonResponse(**lesson)


@router.post("/ask", response_model=CurriculumAskResponse)
def ask_curriculum_question(
    payload: CurriculumAskRequest,
    assistant: CurriculumAssistant = Depends(get_curriculum_assistant),
) -> CurriculumAskResponse:
    """Answer a student's question grounded in Class 6 curriculum evidence.

    Returns the grounded answer, supported boolean, and source chapter/concept metadata.
    """
    provider = get_default_llm_provider()
    result = assistant.answer_question(
        query=payload.question,
        context=payload.context or {},
        provider=provider,
        subject_id=payload.subject_id,
        chapter_id=payload.chapter_id,
        concept_id=payload.concept_id,
    )
    source_meta = None
    if result.source:
        source_meta = CurriculumSourceMetadata(
            subject_id=result.source.subject_id,
            subject_name=result.source.subject_name,
            chapter_id=result.source.chapter_id,
            chapter_title=result.source.chapter_title,
            concept_id=result.source.concept_id,
            concept_title=result.source.concept_title,
        )
    return CurriculumAskResponse(
        question=result.question,
        answer=result.answer,
        supported=result.supported,
        source=source_meta,
        clarification=result.clarification,
    )


@router.post("/resolve", response_model=CurriculumResolveResponse)
def resolve_curriculum_entity(
    payload: CurriculumResolveRequest,
    resolver: CurriculumResolver = Depends(get_curriculum_resolver),
) -> CurriculumResolveResponse:
    """Resolve a subject, unit number, or natural language query against real curriculum records.

    Guarantees:
    - Never defaults to an unrelated lesson when a unit is specified.
    - If a unit does not exist, returns an honest error describing available units.
    """
    resolved = resolver.resolve(
        query=payload.query,
        subject=payload.subject,
        unit_number=payload.unit_number,
        term=payload.term,
    )
    return CurriculumResolveResponse(
        found=resolved.found,
        subject_id=resolved.subject_id,
        subject_name=resolved.subject_name,
        chapter_id=resolved.chapter_id,
        chapter_title=resolved.chapter_title,
        chapter_number=resolved.chapter_number,
        description=resolved.description,
        concept_count=resolved.concept_count,
        first_concept_id=resolved.first_concept_id,
        first_concept_title=resolved.first_concept_title,
        concept_id=resolved.concept_id,
        lesson_id=resolved.lesson_id,
        target_url=resolved.target_url,
        error=resolved.error,
        available_units=resolved.available_units,
    )
