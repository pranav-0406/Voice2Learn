/**
 * QuizView — M05 Adaptive Quiz & Assessment Engine
 *
 * Full adaptive quiz experience across Class 6 subjects:
 *  - Subject selector tabs (Science, Mathematics, English, Social Science)
 *  - Elo-driven question difficulty adaptation
 *  - QuestionCard with high-contrast choice cards and hint drawer
 *  - QuizFeedback with celebratory feedback and pedagogical explanations
 *  - Complete voice command integration
 */

import { useCallback, useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import {
  Award,
  BookOpen,
  CheckCircle,
  RotateCcw,
  Sparkles,
  Trophy,
} from 'lucide-react'
import { Page, PageError } from '../components/ui'
import { QuestionCard } from '../components/quiz/QuestionCard'
import { QuizFeedback } from '../components/quiz/QuizFeedback'
import { getNextQuestion, submitAnswer } from '../api'
import { speakText, speechSupported, stopSpeaking } from '../speech'
import type { AnswerResult, Learner, Question } from '../types'

interface QuizViewProps {
  learner: Learner
}

interface SubjectMeta {
  id: string
  name: string
  accent: string
}

const SUBJECTS: SubjectMeta[] = [
  { id: 'science', name: 'Science', accent: '#059669' },
  { id: 'mathematics', name: 'Mathematics', accent: '#2563EB' },
  { id: 'english', name: 'English', accent: '#7C3AED' },
  { id: 'social_science', name: 'Social Science', accent: '#D97706' },
]

export function QuizView({ learner }: QuizViewProps) {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()

  const activeSubjectId = searchParams.get('subject') || 'science'
  const conceptIdParam = searchParams.get('concept_id') || undefined
  const chapterIdParam = searchParams.get('chapter_id') || undefined

  const [question, setQuestion] = useState<Question | null>(null)
  const [phase, setPhase] = useState<
    'loading' | 'question' | 'feedback' | 'finished' | 'error'
  >('loading')
  const [selectedChoice, setSelectedChoice] = useState<string | null>(null)
  const [hintOpen, setHintOpen] = useState(false)
  const [feedback, setFeedback] = useState<AnswerResult | null>(null)
  const [error, setError] = useState('')
  const [sessionAnswered, setSessionAnswered] = useState(0)
  const [sessionPoints, setSessionPoints] = useState(0)
  const [submitting, setSubmitting] = useState(false)

  const activeSubject =
    SUBJECTS.find((s) => s.id === activeSubjectId) || SUBJECTS[0]

  // Load next question
  const loadNext = useCallback(async () => {
    setPhase('loading')
    setSelectedChoice(null)
    setHintOpen(false)
    setFeedback(null)
    setError('')
    try {
      const response = await getNextQuestion(
        learner.id,
        activeSubjectId,
        conceptIdParam,
        chapterIdParam
      )
      setQuestion(response.question)
      setPhase(response.question ? 'question' : 'finished')
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : 'Could not load a quiz question.'
      )
      setPhase('error')
    }
  }, [learner.id, activeSubjectId, conceptIdParam, chapterIdParam])

  useEffect(() => {
    void loadNext()
  }, [loadNext])

  // Submit selected choice
  const handleSubmitAnswer = useCallback(async () => {
    if (!question || !selectedChoice || submitting) return
    setSubmitting(true)
    try {
      const result = await submitAnswer(
        learner.id,
        question.id,
        selectedChoice
      )
      setFeedback(result)
      setSessionAnswered((prev) => prev + 1)
      setSessionPoints((prev) => prev + result.points_awarded)
      setPhase('feedback')
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : 'Could not evaluate your answer.'
      )
      setPhase('error')
    } finally {
      setSubmitting(false)
    }
  }, [learner.id, question, selectedChoice, submitting])

  // Register voice context & listen for voice actions
  useEffect(() => {
    if (question && phase === 'question') {
      window.dispatchEvent(
        new CustomEvent('voice-context', {
          detail: {
            screen: 'quiz',
            active_quiz: true,
            subject: activeSubject.name,
            question: question.prompt,
            supported_commands: [
              'option A',
              'option B',
              'option C',
              'option D',
              'hint',
              'submit',
              'repeat',
            ],
          },
        })
      )
    }

    const handler = (event: Event) => {
      const action = (event as CustomEvent<{ action: string }>).detail?.action
      if (!action) return

      // Option selection by letter
      const match = action.match(/^SELECT_OPTION_([A-D])$/)
      if (match && question && phase === 'question') {
        const index = match[1].charCodeAt(0) - 65
        const choice = question.choices[index]
        if (choice) setSelectedChoice(choice)
      }

      // Voice Hint
      if (action === 'HINT' || action === 'GIVE_HINT') {
        setHintOpen(true)
        if (speechSupported() && question?.hint) {
          speakText(question.hint)
        }
      }

      // Voice repeat question prompt
      if (action === 'READ_QUESTION' || action === 'REPEAT') {
        if (question?.prompt) speakText(question.prompt)
      }

      // Voice Submit
      if (action === 'SUBMIT_ANSWER' || action === 'CONFIRM') {
        if (selectedChoice && phase === 'question') {
          void handleSubmitAnswer()
        }
      }

      // Voice Next Question
      if (action === 'NEXT_QUESTION' && phase === 'feedback') {
        void loadNext()
      }

      // Voice Stop
      if (action === 'STOP_SPEAKING' || action === 'STOP') {
        stopSpeaking()
      }
    }

    window.addEventListener('voice-command', handler)
    return () => window.removeEventListener('voice-command', handler)
  }, [
    activeSubject.name,
    handleSubmitAnswer,
    loadNext,
    phase,
    question,
    selectedChoice,
  ])

  // Switch subject
  const handleSelectSubject = (subjectId: string) => {
    stopSpeaking()
    const newParams = new URLSearchParams()
    newParams.set('subject', subjectId)
    setSearchParams(newParams)
  }

  return (
    <Page id="quiz-view-page">
      {/* ── Quiz Top Bar: Subject Switcher & Session Stats ── */}
      <div className="quiz-view__topbar">
        <div className="quiz-view__subject-tabs" role="tablist" aria-label="Quiz Subjects">
          {SUBJECTS.map((subj) => {
            const isActive = subj.id === activeSubjectId
            return (
              <button
                key={subj.id}
                type="button"
                role="tab"
                aria-selected={isActive}
                id={`tab-quiz-${subj.id}`}
                className={`quiz-subject-tab ${isActive ? 'active' : ''}`}
                onClick={() => handleSelectSubject(subj.id)}
                style={
                  isActive
                    ? {
                        borderColor: subj.accent,
                        boxShadow: `0 2px 10px ${subj.accent}25`,
                      }
                    : undefined
                }
              >
                <span
                  className="quiz-tab-dot"
                  style={{ backgroundColor: subj.accent }}
                  aria-hidden="true"
                />
                <span>{subj.name}</span>
              </button>
            )
          })}
        </div>

        {/* ── Live Session Stats ── */}
        <div className="quiz-view__stats" aria-label="Current Quiz Session Progress">
          <div className="quiz-stat-pill">
            <Award size={14} aria-hidden="true" />
            <span>{sessionPoints} pts</span>
          </div>
          <div className="quiz-stat-pill">
            <Trophy size={14} aria-hidden="true" />
            <span>{sessionAnswered} answered</span>
          </div>
        </div>
      </div>

      {/* ── Main Quiz States ── */}
      <div className="quiz-view__main">
        {/* Loading Skeleton */}
        {phase === 'loading' && (
          <div className="quiz-skeleton" aria-busy="true" aria-label="Loading question">
            <div className="skeleton quiz-skeleton__header" />
            <div className="skeleton quiz-skeleton__prompt" />
            <div className="skeleton quiz-skeleton__choice" />
            <div className="skeleton quiz-skeleton__choice" />
            <div className="skeleton quiz-skeleton__choice" />
            <div className="skeleton quiz-skeleton__choice" />
          </div>
        )}

        {/* Error State */}
        {phase === 'error' && (
          <PageError message={error} onRetry={loadNext} />
        )}

        {/* Question Phase */}
        {phase === 'question' && question && (
          <QuestionCard
            question={question}
            selectedChoice={selectedChoice}
            onSelectChoice={setSelectedChoice}
            onSubmit={handleSubmitAnswer}
            disabled={submitting}
            hintOpen={hintOpen}
            onToggleHint={() => setHintOpen((prev) => !prev)}
          />
        )}

        {/* Feedback Phase */}
        <AnimatePresence>
          {phase === 'feedback' && feedback && (
            <QuizFeedback
              feedback={feedback}
              onNext={loadNext}
            />
          )}
        </AnimatePresence>

        {/* Finished / Empty Pool Phase */}
        {phase === 'finished' && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="quiz-finished-card"
            role="status"
          >
            <div className="quiz-finished__icon" aria-hidden="true">
              <CheckCircle size={44} color="#059669" />
            </div>
            <p className="eyebrow">ROUND COMPLETE</p>
            <h1>Terrific work, {learner.nickname}!</h1>
            <p className="quiz-finished__summary">
              You answered <strong>{sessionAnswered}</strong> question
              {sessionAnswered === 1 ? '' : 's'} and earned{' '}
              <strong>{sessionPoints}</strong> points for {activeSubject.name}.
            </p>

            <div className="quiz-finished__actions">
              <button
                type="button"
                className="button primary"
                id="btn-quiz-check-more"
                onClick={loadNext}
              >
                <RotateCcw size={16} aria-hidden="true" />
                <span>Check for more questions</span>
              </button>
              <button
                type="button"
                className="button secondary"
                id="btn-quiz-explore-curriculum"
                onClick={() => navigate('/dashboard')}
              >
                <BookOpen size={16} aria-hidden="true" />
                <span>Back to Lessons</span>
              </button>
            </div>

            {/* Other subjects to practice */}
            <div className="quiz-finished__other-subjects">
              <p className="other-subjects-label">
                <Sparkles size={14} aria-hidden="true" />
                <span>Or practice another subject:</span>
              </p>
              <div className="other-subjects-list">
                {SUBJECTS.filter((s) => s.id !== activeSubjectId).map((subj) => (
                  <button
                    key={subj.id}
                    type="button"
                    className="other-subject-btn"
                    onClick={() => handleSelectSubject(subj.id)}
                  >
                    {subj.name}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </Page>
  )
}
