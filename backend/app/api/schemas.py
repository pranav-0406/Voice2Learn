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


class VoiceInterpretRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    context: VoiceContext = Field(default_factory=VoiceContext)


class VoiceInterpretResponse(BaseModel):
    intent: Literal["command", "quiz_answer", "question", "unknown"]
    confidence: float
    command: str | None = None
    answer: str | None = None
