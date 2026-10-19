/// <reference types="vite/client" />
import { voiceDiagnostic } from './voiceDiagnostics'

export type GradeBand = '6-7' | '8-9'
export type Difficulty = 'easy' | 'medium' | 'hard'
export interface Learner { id: string; nickname: string; grade_band: GradeBand }
export interface Subject { id: string; name: string; language: string }
export interface Lesson { id: string; subject: string; topic: string; title: string; content: { summary?: string; key_points?: string[]; vocabulary?: Record<string, string>; try_it?: string; quiz_ready_facts?: string[] } }
export interface Question { id: string; lesson_id: string; topic: string; difficulty: Difficulty; prompt: string; choices: string[] }
export interface Progress { points: number; ability: number; correct_streak: number; incorrect_streak: number; target_difficulty: Difficulty; topics: Array<{ topic: string; attempts: number; correct_answers: number; mastery_percent: number }>; lessons: Array<{ lesson_id: string; attempts: number; correct_answers: number; mastery_percent: number }> }
export interface VoiceContext { active_quiz?: boolean; screen?: string; lesson_topic?: string | null; question?: string | null; recent_turns?: string[] }
export interface Interpretation { intent: 'command' | 'quiz_answer' | 'question' | 'unknown'; confidence: number; command: string | null; answer: string | null; category?: 'application' | 'learning' | 'follow_up' | 'clarification' | 'unsupported' | null; response?: string | null; clarification?: string | null }
export interface AnswerResult { correct: boolean; points_awarded: number; ability: number; target_difficulty: Difficulty; duplicate_submission: boolean; message: string }

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...init?.headers } })
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
export const getNextQuestion = (learnerId: string, subject = 'science') => request<{ question: Question | null; message: string }>(`/api/quiz/next?learner_id=${encodeURIComponent(learnerId)}&subject=${encodeURIComponent(subject)}`)
export const submitAnswer = (learner_id: string, question_id: string, answer: string) => request<AnswerResult>('/api/quiz/answer', { method: 'POST', body: JSON.stringify({ learner_id, question_id, answer }) })
export async function interpretVoice(text: string, active_quiz = false, context: VoiceContext = {}) {
  const startedAt = voiceDiagnostic('intent-classification-start')
  const result = await request<Interpretation>('/api/voice/interpret', { method: 'POST', body: JSON.stringify({ text, context: { ...context, active_quiz } }) })
  voiceDiagnostic('intent-classification-complete', startedAt)
  return result
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
