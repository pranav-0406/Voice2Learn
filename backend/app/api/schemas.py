"""Request and response models for the currently implemented API."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class LearnerCreate(BaseModel):
    nickname: str = Field(min_length=1, max_length=40, description="A non-identifying display name")
    grade_band: Literal["6-7", "8-9"] = "6-7"


class LearnerResponse(BaseModel):
    id: str
    nickname: str
    grade_band: Literal["6-7", "8-9"]


class SubjectResponse(BaseModel):
    id: str
    name: str
    language: Literal["English"]


class SubjectsResponse(BaseModel):
    subjects: list[SubjectResponse]


class LessonResponse(BaseModel):
    id: str
    subject: str
    topic: str
    title: str
    content: dict[str, object]


class QuizQuestionResponse(BaseModel):
    id: str
    lesson_id: str
    topic: str
    difficulty: Literal["easy", "medium", "hard"]
    prompt: str
    choices: list[str]
    hint: str | None = None


class QuizNextResponse(BaseModel):
    question: QuizQuestionResponse | None
    message: str


class QuizAnswerRequest(BaseModel):
    learner_id: UUID
    question_id: str = Field(min_length=1, max_length=100)
    answer: str = Field(min_length=1, max_length=200)


class QuizAnswerResponse(BaseModel):
    correct: bool
    points_awarded: int
    ability: float
    target_difficulty: Literal["easy", "medium", "hard"]
    duplicate_submission: bool
    message: str
    explanation: str | None = None
    correct_answer: str | None = None


class TopicProgressResponse(BaseModel):
    topic: str
    attempts: int
    correct_answers: int
    mastery_percent: float


class LessonProgressResponse(BaseModel):
    lesson_id: str
    attempts: int
    correct_answers: int
    mastery_percent: float


class ProgressResponse(BaseModel):
    learner_id: str
    ability: float
    points: int
    correct_streak: int
    incorrect_streak: int
    target_difficulty: Literal["easy", "medium", "hard"]
    topics: list[TopicProgressResponse]
    lessons: list[LessonProgressResponse]


class TranscriptionMetadata(BaseModel):
    language: str | None
    duration_seconds: float | None
    model: str
    device: str


class TranscriptionResponse(BaseModel):
    text: str
    metadata: TranscriptionMetadata


class VoiceContext(BaseModel):
    active_quiz: bool = False
    screen: str = "unknown"
    lesson_topic: str | None = None
    question: str | None = None
    recent_turns: list[str] = Field(default_factory=list, max_length=4)


class VoiceInterpretRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    context: VoiceContext = Field(default_factory=VoiceContext)


class CurriculumSourceMetadata(BaseModel):
    subject_id: str
    subject_name: str
    chapter_id: str
    chapter_title: str
    concept_id: str | None = None
    concept_title: str | None = None


class VoiceInterpretResponse(BaseModel):
    intent: Literal["command", "quiz_answer", "question", "unknown", "noise"]
    confidence: float
    command: str | None = None
    answer: str | None = None
    category: Literal["application", "learning", "follow_up", "clarification", "unsupported", "noise"] | None = None
    response: str | None = None
    clarification: str | None = None
    source: CurriculumSourceMetadata | None = None


# ─────────────────────────────────────────────────────────────────────────────
# M09 Curriculum RAG Question Answering schemas
# ─────────────────────────────────────────────────────────────────────────────

class CurriculumAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    subject_id: str | None = None
    chapter_id: str | None = None
    concept_id: str | None = None
    context: dict[str, object] | None = None


class CurriculumAskResponse(BaseModel):
    question: str
    answer: str
    supported: bool
    source: CurriculumSourceMetadata | None = None
    clarification: str | None = None


class CurriculumResolveRequest(BaseModel):
    query: str | None = None
    subject: str | None = None
    unit_number: int | None = None
    term: int = 1


class CurriculumResolveResponse(BaseModel):
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


class LearnerPositionSaveRequest(BaseModel):
    learner_id: str
    subject_id: str
    chapter_id: str
    concept_id: str


class LearnerPositionResponse(BaseModel):
    learner_id: str
    subject_id: str
    chapter_id: str
    concept_id: str
    updated_at: str
    chapter_title: str | None = None
    chapter_number: int | None = None
    concept_title: str | None = None
    concept_summary: str | None = None
    subject_name: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Curriculum schemas (M01)
# ─────────────────────────────────────────────────────────────────────────────

class CurriculumSubjectResponse(BaseModel):
    id: str
    name: str
    code: str
    icon: str
    accent_color: str
    display_order: int
    chapter_count: int
    terms_available: list[int]


class CurriculumSubjectsResponse(BaseModel):
    subjects: list[CurriculumSubjectResponse]


class CurriculumChapterResponse(BaseModel):
    id: str
    subject_id: str
    term: int
    chapter_number: int
    title: str
    description: str | None = None
    textbook_pages: str | None = None
    lesson_id: str | None = None
    concept_count: int


class CurriculumTermChaptersResponse(BaseModel):
    subject_id: str
    term: int
    chapters: list[CurriculumChapterResponse]


class CurriculumConceptResponse(BaseModel):
    id: str
    chapter_id: str
    title: str
    summary: str
    key_points: list[str]
    display_order: int


class CurriculumChapterDetailResponse(BaseModel):
    id: str
    subject_id: str
    term: int
    chapter_number: int
    title: str
    description: str | None = None
    textbook_pages: str | None = None
    lesson_id: str | None = None
    concepts: list[CurriculumConceptResponse]


# ─────────────────────────────────────────────────────────────────────────────
# M04 Concept-Lesson schemas
# ─────────────────────────────────────────────────────────────────────────────

class ConceptNavRef(BaseModel):
    id: str
    title: str
    display_order: int


class ConceptLessonResponse(BaseModel):
    id: str
    chapter_id: str
    title: str
    summary: str
    key_points: list[str]
    display_order: int
    index: int
    total: int
    chapter_title: str
    chapter_description: str | None = None
    textbook_pages: str | None = None
    term: int
    chapter_number: int
    subject_id: str
    subject_name: str
    subject_icon: str
    subject_accent: str
    prev_concept: ConceptNavRef | None = None
    next_concept: ConceptNavRef | None = None
    all_concepts: list[ConceptNavRef]


# ─────────────────────────────────────────────────────────────────────────────
# Student Authentication schemas (M03)
# ─────────────────────────────────────────────────────────────────────────────

class StudentRegisterRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=40, description="Display nickname")
    pin: str = Field(min_length=4, max_length=12, pattern="^[0-9]+$", description="Numeric PIN")
    grade_band: Literal["6-7", "8-9"] = "6-7"
    board: str = "TN_STATE_BOARD"
    class_level: int = 6


class StudentLoginRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=40)
    pin: str = Field(min_length=4, max_length=12)


class StudentProfile(BaseModel):
    id: str
    nickname: str
    board: str
    class_level: int
    grade_band: str
    created_at: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student: StudentProfile

