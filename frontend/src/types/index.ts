/**
 * Voice2Learn Domain Types — English-Only Edition
 * Supported Class 6 Subjects: English, Mathematics, Science, Social Science
 */

export type GradeBand = '6-7' | '8-9'
export type Difficulty = 'easy' | 'medium' | 'hard'

export type SubjectId = 'english' | 'mathematics' | 'science' | 'social_science'

export interface Subject {
  id: string
  name: string
  language: 'English'
  description?: string
  unitCount?: number
  icon?: string
}

export interface LessonContent {
  summary?: string
  key_points?: string[]
  vocabulary?: Record<string, string>
  try_it?: string
  quiz_ready_facts?: string[]
}

export interface Lesson {
  id: string
  subject: string
  topic: string
  title: string
  content: LessonContent
  term?: number
  unit_number?: number
}

export interface Question {
  id: string
  lesson_id: string
  topic: string
  difficulty: Difficulty
  prompt: string
  choices: string[]
  hint?: string | null
}

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
  points: number
  ability: number
  correct_streak: number
  incorrect_streak: number
  target_difficulty: Difficulty
  topics: TopicProgress[]
  lessons: LessonProgress[]
}

export interface VoiceContext {
  active_quiz?: boolean
  screen?: string
  lesson_topic?: string | null
  question?: string | null
  recent_turns?: string[]
}

export interface CurriculumSourceMetadata {
  subject_id: string
  subject_name: string
  chapter_id: string
  chapter_title: string
  concept_id?: string | null
  concept_title?: string | null
}

export interface Interpretation {
  intent: 'command' | 'quiz_answer' | 'question' | 'unknown'
  confidence: number
  command: string | null
  answer: string | null
  category?: 'application' | 'learning' | 'follow_up' | 'clarification' | 'unsupported' | null
  response?: string | null
  clarification?: string | null
  source?: CurriculumSourceMetadata | null
}

export interface CurriculumAskRequest {
  question: string
  subject_id?: string | null
  chapter_id?: string | null
  concept_id?: string | null
  context?: Record<string, unknown> | null
}

export interface CurriculumAskResponse {
  question: string
  answer: string
  supported: boolean
  source?: CurriculumSourceMetadata | null
  clarification?: string | null
}

export interface CurriculumResolveResponse {
  found: boolean
  subject_id?: string | null
  subject_name?: string | null
  chapter_id?: string | null
  chapter_title?: string | null
  chapter_number?: number | null
  description?: string | null
  concept_count: number
  first_concept_id?: string | null
  first_concept_title?: string | null
  lesson_id?: string | null
  target_url?: string | null
  error?: string | null
  available_units: number
}

export interface LearnerPositionResponse {
  learner_id: string
  subject_id: string
  chapter_id: string
  concept_id: string
  updated_at: string
  chapter_title?: string | null
  chapter_number?: number | null
  concept_title?: string | null
  concept_summary?: string | null
  subject_name?: string | null
}

export interface AnswerResult {
  correct: boolean
  points_awarded: number
  ability: number
  target_difficulty: Difficulty
  duplicate_submission: boolean
  message: string
  explanation?: string | null
  correct_answer?: string | null
}

export interface Learner {
  id: string
  nickname: string
  grade_band: GradeBand
}

export interface VoiceCommandAction {
  action: string
  payload?: Record<string, unknown>
}

// ─────────────────────────────────────────────────────────────────────────────
// Dynamic Curriculum Engine Types (M01)
// ─────────────────────────────────────────────────────────────────────────────

export interface CurriculumSubject {
  id: string
  name: string
  code: string
  icon: string
  accent_color: string
  display_order: number
  chapter_count: number
  terms_available: number[]
}

export interface CurriculumChapter {
  id: string
  subject_id: string
  term: number
  chapter_number: number
  title: string
  description?: string | null
  textbook_pages?: string | null
  lesson_id?: string | null
  concept_count: number
}

export interface CurriculumConcept {
  id: string
  chapter_id: string
  title: string
  summary: string
  key_points: string[]
  display_order: number
}

export interface CurriculumChapterDetail extends CurriculumChapter {
  concepts: CurriculumConcept[]
}

// ─────────────────────────────────────────────────────────────────────────────
// Student Authentication Types (M03)
// ─────────────────────────────────────────────────────────────────────────────

export interface StudentProfile {
  id: string
  nickname: string
  board: string
  class_level: number
  grade_band: GradeBand
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  student: StudentProfile
}

// ─────────────────────────────────────────────────────────────────────────────
// M04 Concept-Lesson Viewer Types
// ─────────────────────────────────────────────────────────────────────────────

export interface ConceptNavRef {
  id: string
  title: string
  display_order: number
}

export interface ConceptLesson {
  id: string
  chapter_id: string
  title: string
  summary: string
  key_points: string[]
  display_order: number
  index: number
  total: number
  chapter_title: string
  chapter_description?: string | null
  textbook_pages?: string | null
  term: number
  chapter_number: number
  subject_id: string
  subject_name: string
  subject_icon: string
  subject_accent: string
  prev_concept: ConceptNavRef | null
  next_concept: ConceptNavRef | null
  all_concepts: ConceptNavRef[]
}

export type NarrationState = 'idle' | 'speaking' | 'paused'
