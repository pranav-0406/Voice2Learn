import type {
  GradeBand,
  HealthResponse,
  Learner,
  Lesson,
  Progress,
  QuizAnswerResponse,
  QuizNextResponse,
  Subject,
  TranscriptionResponse,
  VoiceInterpretResponse,
} from '../types'

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

// ─── Generic fetch wrapper ────────────────────────────────────────────────────

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      // ignore JSON parse failures
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

// ─── Health ───────────────────────────────────────────────────────────────────

export const getHealth = (): Promise<HealthResponse> =>
  request<HealthResponse>('/api/health')

// ─── Learners ─────────────────────────────────────────────────────────────────

export const createLearner = (nickname: string, grade_band: GradeBand): Promise<Learner> =>
  request<Learner>('/api/learners', {
    method: 'POST',
    body: JSON.stringify({ nickname, grade_band }),
  })

// ─── Subjects & Lessons ───────────────────────────────────────────────────────

export const getSubjects = (): Promise<{ subjects: Subject[] }> =>
  request<{ subjects: Subject[] }>('/api/subjects')

export const getLesson = (lessonId: string): Promise<Lesson> =>
  request<Lesson>(`/api/lessons/${lessonId}`)

// ─── Quiz ─────────────────────────────────────────────────────────────────────

export const getNextQuestion = (learnerId: string, subject: string): Promise<QuizNextResponse> =>
  request<QuizNextResponse>(
    `/api/quiz/next?learner_id=${encodeURIComponent(learnerId)}&subject=${encodeURIComponent(subject)}`
  )

export const submitAnswer = (
  learnerId: string,
  questionId: string,
  answer: string
): Promise<QuizAnswerResponse> =>
  request<QuizAnswerResponse>('/api/quiz/answer', {
    method: 'POST',
    body: JSON.stringify({ learner_id: learnerId, question_id: questionId, answer }),
  })

// ─── Progress ─────────────────────────────────────────────────────────────────

export const getProgress = (learnerId: string): Promise<Progress> =>
  request<Progress>(`/api/progress/${learnerId}`)

// ─── Voice ────────────────────────────────────────────────────────────────────

export const transcribeAudio = async (audioBlob: Blob): Promise<TranscriptionResponse> => {
  const form = new FormData()
  // Prefer webm; backend accepts audio/webm and audio/wav
  const file = new File([audioBlob], 'recording.webm', { type: 'audio/webm' })
  form.append('audio', file)
  const res = await fetch(`${BASE}/api/voice/transcribe`, { method: 'POST', body: form })
  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch { /* ignore */ }
    throw new Error(detail)
  }
  return res.json() as Promise<TranscriptionResponse>
}

export const interpretVoice = (
  text: string,
  activeQuiz = false
): Promise<VoiceInterpretResponse> =>
  request<VoiceInterpretResponse>('/api/voice/interpret', {
    method: 'POST',
    body: JSON.stringify({ text, context: { active_quiz: activeQuiz } }),
  })
