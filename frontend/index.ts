// ─── Learner ────────────────────────────────────────────────────────────────

export type GradeBand = '6-7' | '8-9'

export interface Learner {
  id: string
  nickname: string
  grade_band: GradeBand
}

// ─── Subjects & Lessons ─────────────────────────────────────────────────────

export interface Subject {
  id: string
  name: string
  language: 'English'
}

export interface LessonContent {
  summary?: string
  key_points?: string[]
  vocabulary?: Record<string, string>
  try_it?: string
  quiz_ready_facts?: string[]
  [key: string]: unknown
}

export interface Lesson {
  id: string
  subject: string
  topic: string
  title: string
  content: LessonContent
}

// ─── Quiz ────────────────────────────────────────────────────────────────────

export type Difficulty = 'easy' | 'medium' | 'hard'

export interface QuizQuestion {
  id: string
  lesson_id: string
  topic: string
  difficulty: Difficulty
  prompt: string
  choices: string[]
}

export interface QuizNextResponse {
  question: QuizQuestion | null
  message: string
}

export interface QuizAnswerResponse {
  correct: boolean
  points_awarded: number
  ability: number
  target_difficulty: Difficulty
  duplicate_submission: boolean
  message: string
}

// ─── Progress ────────────────────────────────────────────────────────────────

export interface TopicProgress {
  topic: string
  attempts: number
  correct_answers: number
  mastery_percent: number
}

export interface LessonProgress {
  lesson_id: string
  attempts: number
  correct_answers: number
  mastery_percent: number
}

export interface Progress {
  learner_id: string
  ability: number
  points: number
  correct_streak: number
  incorrect_streak: number
  target_difficulty: Difficulty
  topics: TopicProgress[]
  lessons: LessonProgress[]
}

// ─── Voice ───────────────────────────────────────────────────────────────────

export type VoiceIntent = 'command' | 'quiz_answer' | 'question' | 'unknown'

export interface TranscriptionMetadata {
  language: string | null
  duration_seconds: number | null
  model: string
  device: string
}

export interface TranscriptionResponse {
  text: string
  metadata: TranscriptionMetadata
}

export interface VoiceInterpretResponse {
  intent: VoiceIntent
  confidence: number
  command: string | null
  answer: string | null
}

// ─── Health ──────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: 'ok'
  message: string
  stt_backend: string
  llm_backend: string
  retrieval_ready: boolean
}

// ─── Session (local storage) ─────────────────────────────────────────────────

export interface Session {
  learner: Learner
  savedAt: string
}
