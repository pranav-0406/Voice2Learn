/// <reference types="vite/client" />
import { voiceDiagnostic } from './voiceDiagnostics'

export type {
  GradeBand,
  Difficulty,
  SubjectId,
  Learner,
  Subject,
  Lesson,
  LessonContent,
  Question,
  Progress,
  TopicProgress,
  LessonProgress,
  VoiceContext,
  Interpretation,
  AnswerResult,
  VoiceCommandAction,
  CurriculumSourceMetadata,
  CurriculumAskRequest,
  CurriculumAskResponse,
  CurriculumResolveResponse,
  LearnerPositionResponse,
} from './types'

import type {
  GradeBand,
  Learner,
  Subject,
  Lesson,
  Question,
  Progress,
  VoiceContext,
  Interpretation,
  AnswerResult,
  CurriculumAskResponse,
  CurriculumResolveResponse,
  LearnerPositionResponse,
} from './types'

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const TOKEN_KEY = 'voice2learn_auth_token'
export const getAuthToken = (): string | null => localStorage.getItem(TOKEN_KEY)
export const setAuthToken = (token: string): void => localStorage.setItem(TOKEN_KEY, token)
export const clearAuthToken = (): void => localStorage.removeItem(TOKEN_KEY)

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAuthToken()
  const authHeaders: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {}
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...authHeaders, ...init?.headers },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail || `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}
export const createLearner = (nickname: string, grade_band: GradeBand) => request<Learner>('/api/learners', { method: 'POST', body: JSON.stringify({ nickname, grade_band }) })
export const getSubjects = () => request<{ subjects: Subject[] }>('/api/subjects')
export const getLesson = (id: string) => request<Lesson>(`/api/lessons/${encodeURIComponent(id)}`)
export const getProgress = (learnerId: string) => request<Progress>(`/api/progress/${encodeURIComponent(learnerId)}`)
export const getNextQuestion = (
  learnerId: string,
  subject = 'science',
  conceptId?: string | null,
  chapterId?: string | null,
) => {
  const params = new URLSearchParams({
    learner_id: learnerId,
    subject: subject,
  })
  if (conceptId) params.append('concept_id', conceptId)
  if (chapterId) params.append('chapter_id', chapterId)
  return request<{ question: Question | null; message: string }>(`/api/quiz/next?${params.toString()}`)
}
export const submitAnswer = (learner_id: string, question_id: string, answer: string) => request<AnswerResult>('/api/quiz/answer', { method: 'POST', body: JSON.stringify({ learner_id, question_id, answer }) })
export async function interpretVoice(text: string, active_quiz = false, context: VoiceContext = {}) {
  const startedAt = voiceDiagnostic('intent-classification-start')
  const result = await request<Interpretation>('/api/voice/interpret', { method: 'POST', body: JSON.stringify({ text, context: { ...context, active_quiz } }) })
  voiceDiagnostic('intent-classification-complete', startedAt)
  return result
}
export async function askCurriculumQuestion(
  question: string,
  options?: {
    subject_id?: string | null
    chapter_id?: string | null
    concept_id?: string | null
    context?: Record<string, unknown> | null
  }
) {
  return request<CurriculumAskResponse>('/api/curriculum/ask', {
    method: 'POST',
    body: JSON.stringify({
      question,
      subject_id: options?.subject_id,
      chapter_id: options?.chapter_id,
      concept_id: options?.concept_id,
      context: options?.context,
    }),
  })
}
export async function resolveCurriculum(options: {
  query?: string | null
  subject?: string | null
  unit_number?: number | null
  term?: number
}) {
  return request<CurriculumResolveResponse>('/api/curriculum/resolve', {
    method: 'POST',
    body: JSON.stringify(options),
  })
}
export async function saveActivePosition(
  learner_id: string,
  subject_id: string,
  chapter_id: string,
  concept_id: string
) {
  return request<LearnerPositionResponse>('/api/progress/position', {
    method: 'POST',
    body: JSON.stringify({ learner_id, subject_id, chapter_id, concept_id }),
  })
}
export async function getActivePosition(learner_id: string, subject_id?: string) {
  const query = subject_id ? `?subject_id=${encodeURIComponent(subject_id)}` : ''
  return request<LearnerPositionResponse | null>(`/api/progress/${encodeURIComponent(learner_id)}/position${query}`)
}
export async function transcribeAudio(audio: Blob) {
  const form = new FormData()
  const mime = audio.type === 'audio/wav' ? 'audio/wav' : 'audio/webm'
  form.append('audio', new File([audio], mime === 'audio/wav' ? 'voice-note.wav' : 'voice-note.webm', { type: mime }))
  const uploadStartedAt = voiceDiagnostic('audio-upload-start')
  const response = await fetch(`${baseUrl}/api/voice/transcribe`, { method: 'POST', body: form })
  if (!response.ok) { const body = await response.json().catch(() => null); throw new Error(body?.detail || 'Could not transcribe audio.') }
  const result = await response.json() as { text: string }
  voiceDiagnostic('transcription-complete', uploadStartedAt)
  return result
}

// ─────────────────────────────────────────────────────────────────────────────
// AI Browser Agent API
// ─────────────────────────────────────────────────────────────────────────────

export interface AgentRunContext {
  learner_id?: string
  current_url?: string
  page_title?: string
  dom_summary?: string | null
  interactive_elements?: Array<Record<string, unknown>>
  active_position?: Record<string, unknown> | null
}

export interface AgentAction {
  action_type: 'navigate' | 'click' | 'scroll' | 'read_aloud' | 'speak_to_user' | 'complete_task' | 'ask_clarification'
  thought: string
  target_url?: string | null
  selector?: string | null
  element_text?: string | null
  scroll_direction?: string | null
  text_to_speak?: string | null
  message?: string | null
  success?: boolean
}

export interface AgentStep {
  step_number: number
  thought: string
  action: AgentAction
}

export interface AgentRunResponse {
  run_id: string
  status: 'completed' | 'needs_clarification' | 'failed'
  steps: AgentStep[]
  final_message: string
  target_url?: string | null
  total_steps: number
}

export async function runAgent(prompt: string, context: AgentRunContext = {}) {
  const startedAt = voiceDiagnostic('agent-run-start')
  const result = await request<AgentRunResponse>('/api/agent/run', {
    method: 'POST',
    body: JSON.stringify({
      prompt,
      context: {
        learner_id: context.learner_id || 'demo-learner',
        current_url: context.current_url || (typeof window !== 'undefined' ? window.location.pathname : '/dashboard'),
        page_title: context.page_title || (typeof document !== 'undefined' ? document.title : 'Dashboard'),
        ...context,
      },
    }),
  })
  voiceDiagnostic('agent-run-complete', startedAt)
  return result
}

// ─────────────────────────────────────────────────────────────────────────────
// Dynamic Curriculum Engine API (M01)
// ─────────────────────────────────────────────────────────────────────────────

export type {
  CurriculumSubject,
  CurriculumChapter,
  CurriculumConcept,
  CurriculumChapterDetail,
} from './types'

import type {
  CurriculumSubject,
  CurriculumChapter,
  CurriculumConcept,
  CurriculumChapterDetail,
} from './types'

export const fetchCurriculumSubjects = () =>
  request<{ subjects: CurriculumSubject[] }>('/api/curriculum/subjects').then((res) => res.subjects)

export const fetchCurriculumSubject = (subjectId: string) =>
  request<CurriculumSubject>(`/api/curriculum/subjects/${encodeURIComponent(subjectId)}`)

export const fetchTermChapters = (subjectId: string, term: number = 1) =>
  request<{ subject_id: string; term: number; chapters: CurriculumChapter[] }>(
    `/api/curriculum/subjects/${encodeURIComponent(subjectId)}/terms/${term}`
  ).then((res) => res.chapters)

export const fetchChapterDetail = (chapterId: string) =>
  request<CurriculumChapterDetail>(`/api/curriculum/chapters/${encodeURIComponent(chapterId)}`)

export const fetchConceptDetail = (conceptId: string) =>
  request<CurriculumConcept>(`/api/curriculum/concepts/${encodeURIComponent(conceptId)}`)

// ─────────────────────────────────────────────────────────────────────────────
// Student Authentication API (M03)
// ─────────────────────────────────────────────────────────────────────────────

export type {
  StudentProfile,
  AuthResponse,
} from './types'

import type {
  StudentProfile,
  AuthResponse,
} from './types'

export const registerStudent = (
  nickname: string,
  pin: string,
  grade_band: GradeBand = '6-7'
) =>
  request<AuthResponse>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ nickname, pin, grade_band }),
  }).then((res) => {
    setAuthToken(res.access_token)
    return res
  })

export const loginStudent = (nickname: string, pin: string) =>
  request<AuthResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ nickname, pin }),
  }).then((res) => {
    setAuthToken(res.access_token)
    return res
  })

export const fetchCurrentStudent = () =>
  request<StudentProfile>('/api/auth/me')

export const logoutStudent = () => {
  clearAuthToken()
}

// ─────────────────────────────────────────────────────────────────────────────
// M04 Concept-Lesson API
// ─────────────────────────────────────────────────────────────────────────────

export type { ConceptLesson, ConceptNavRef, NarrationState } from './types'
import type { ConceptLesson } from './types'

export const fetchConceptLesson = (conceptId: string) =>
  request<ConceptLesson>(`/api/curriculum/concepts/${encodeURIComponent(conceptId)}/lesson`)
