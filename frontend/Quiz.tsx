import { useCallback, useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle2, XCircle, ChevronRight, Zap, RotateCcw, Volume2 } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Card, Badge } from '../components/ui/Card'
import { getNextQuestion, submitAnswer } from '../services/api'
import { useTTS } from '../hooks/useTTS'
import type { Learner, QuizAnswerResponse, QuizQuestion, Difficulty } from '../types'

interface QuizProps { learner: Learner }

type QuizPhase = 'loading' | 'question' | 'feedback' | 'finished' | 'error'

const difficultyBadge: Record<Difficulty, { color: 'emerald' | 'amber' | 'violet'; label: string }> = {
  easy:   { color: 'emerald', label: 'Foundation' },
  medium: { color: 'amber',   label: 'Intermediate' },
  hard:   { color: 'violet',  label: 'Advanced' },
}

export default function Quiz({ learner }: QuizProps) {
  const [phase, setPhase] = useState<QuizPhase>('loading')
  const [question, setQuestion] = useState<QuizQuestion | null>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<QuizAnswerResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [answered, setAnswered] = useState(0)
  const [totalPoints, setTotalPoints] = useState(0)
  const { speak } = useTTS()
  const firstChoiceRef = useRef<HTMLButtonElement>(null)

  const fetchNext = useCallback(async () => {
    setPhase('loading')
    setSelected(null)
    setFeedback(null)
    try {
      const res = await getNextQuestion(learner.id, 'science')
      if (!res.question) {
        setPhase('finished')
        return
      }
      setQuestion(res.question)
      setPhase('question')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load question.')
      setPhase('error')
    }
  }, [learner.id])

  useEffect(() => { fetchNext() }, [fetchNext])

  // Auto-focus first choice when question loads
  useEffect(() => {
    if (phase === 'question') {
      setTimeout(() => firstChoiceRef.current?.focus(), 100)
    }
  }, [phase, question?.id])

  // Speak question when it loads
  useEffect(() => {
    if (phase === 'question' && question) speak(question.prompt)
  }, [phase, question?.id])

  async function handleAnswer(choice: string) {
    if (!question || submitting || selected) return
    setSelected(choice)
    setSubmitting(true)
    try {
      const res = await submitAnswer(learner.id, question.id, choice)
      setFeedback(res)
      setAnswered(a => a + 1)
      if (res.points_awarded > 0) setTotalPoints(p => p + res.points_awarded)
      setPhase('feedback')
      speak(res.correct ? 'Correct! Well done.' : `Not quite. ${res.message}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not submit answer.')
      setPhase('error')
    } finally {
      setSubmitting(false)
    }
  }

  // ─── States ───────────────────────────────────────────────────────────────

  if (phase === 'loading') {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-6 w-32 bg-base-200 rounded-xl" />
        <div className="h-24 bg-base-100 rounded-2xl" />
        <div className="space-y-3">
          {[0, 1, 2].map(i => <div key={i} className="h-16 bg-base-100 rounded-2xl" />)}
        </div>
      </div>
    )
  }

  if (phase === 'error') {
    return (
      <div className="text-center py-12">
        <p className="text-rose-500 text-sm mb-4">{error}</p>
        <Button onClick={fetchNext} variant="secondary">
          <RotateCcw className="w-4 h-4" />
          Try again
        </Button>
      </div>
    )
  }

  if (phase === 'finished') {
    return (
      <motion.div
        className="text-center py-8 space-y-6"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
      >
        <div className="w-20 h-20 rounded-full bg-emerald-500/10 flex items-center justify-center mx-auto">
          <CheckCircle2 className="w-10 h-10 text-emerald-500" />
        </div>
        <div>
          <h2 className="text-2xl font-extrabold text-navy-900 mb-1">All done!</h2>
          <p className="text-navy-700/50 text-sm">You've answered all available questions.</p>
        </div>
        <Card className="p-6 inline-block mx-auto">
          <p className="text-3xl font-extrabold text-amber-500 mb-1">{totalPoints}</p>
          <p className="text-sm text-navy-700/50">points earned this session</p>
          <p className="text-xs text-navy-700/40 mt-1">{answered} question{answered !== 1 ? 's' : ''} answered</p>
        </Card>
        <Button onClick={fetchNext} variant="secondary">
          <RotateCcw className="w-4 h-4" />
          Try again
        </Button>
      </motion.div>
    )
  }

  // ─── Question ──────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-navy-900 tracking-tight">Quiz</h1>
          {answered > 0 && (
            <p className="text-xs text-navy-700/50 mt-0.5">{answered} answered · {totalPoints} pts</p>
          )}
        </div>
        {question && (
          <Badge color={difficultyBadge[question.difficulty].color}>
            <Zap className="w-3 h-3" />
            {difficultyBadge[question.difficulty].label}
          </Badge>
        )}
      </div>

      <AnimatePresence mode="wait">
        {question && (
          <motion.div
            key={question.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.25 }}
            className="space-y-4"
          >
            {/* Question card */}
            <Card className="p-5">
              <div className="flex items-start justify-between gap-3 mb-1">
                <p className="text-xs text-navy-700/40 font-medium">{question.topic}</p>
                <button
                  onClick={() => speak(question.prompt)}
                  className="shrink-0 p-1 rounded-lg hover:bg-base-100 text-navy-700/40 hover:text-primary-600 transition-colors"
                  aria-label="Hear question aloud"
                >
                  <Volume2 className="w-4 h-4" />
                </button>
              </div>
              <p className="text-lg font-bold text-navy-900 leading-snug">{question.prompt}</p>
            </Card>

            {/* Choices */}
            <div className="space-y-2.5" role="group" aria-label="Answer choices">
              {question.choices.map((choice, i) => {
                const isSelected = selected === choice
                const hasFeedback = phase === 'feedback' && feedback
                const isCorrect = hasFeedback && isSelected && feedback.correct
                const isWrong = hasFeedback && isSelected && !feedback.correct

                return (
                  <motion.button
                    key={choice}
                    ref={i === 0 ? firstChoiceRef : undefined}
                    className={[
                      'w-full text-left px-5 py-4 rounded-2xl border-2 font-medium text-sm transition-colors duration-150',
                      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2',
                      isCorrect
                        ? 'border-emerald-500 bg-emerald-50 text-emerald-800'
                        : isWrong
                        ? 'border-rose-400 bg-rose-50 text-rose-800'
                        : isSelected
                        ? 'border-primary-500 bg-primary-50 text-primary-800'
                        : hasFeedback
                        ? 'border-base-200 bg-white text-navy-700/50 cursor-default'
                        : 'border-base-200 bg-white text-navy-900 hover:border-primary-400 hover:bg-base-50',
                    ].join(' ')}
                    onClick={() => handleAnswer(choice)}
                    disabled={!!selected || submitting}
                    aria-pressed={isSelected}
                    whileTap={!selected ? { scale: 0.98 } : undefined}
                    transition={{ duration: 0.1 }}
                  >
                    <span className="flex items-center gap-3">
                      <span className={[
                        'w-7 h-7 rounded-full text-xs font-bold flex items-center justify-center shrink-0',
                        isCorrect ? 'bg-emerald-500 text-white' : isWrong ? 'bg-rose-400 text-white' : 'bg-base-100 text-navy-700',
                      ].join(' ')}>
                        {String.fromCharCode(65 + i)}
                      </span>
                      {choice}
                      {isCorrect && <CheckCircle2 className="w-4 h-4 text-emerald-500 ml-auto shrink-0" />}
                      {isWrong && <XCircle className="w-4 h-4 text-rose-400 ml-auto shrink-0" />}
                    </span>
                  </motion.button>
                )
              })}
            </div>

            {/* Feedback */}
            <AnimatePresence>
              {phase === 'feedback' && feedback && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-3"
                >
                  <Card className={['p-4', feedback.correct ? 'bg-emerald-50 border-emerald-200' : 'bg-rose-50 border-rose-200'].join(' ')}>
                    <p className={['text-sm font-semibold mb-1', feedback.correct ? 'text-emerald-700' : 'text-rose-700'].join(' ')}>
                      {feedback.correct ? '✓ Correct!' : '✗ Not quite'}
                    </p>
                    <p className="text-sm text-navy-700">{feedback.message}</p>
                    {feedback.points_awarded > 0 && (
                      <p className="text-xs text-amber-600 font-semibold mt-1">+{feedback.points_awarded} points</p>
                    )}
                  </Card>

                  <Button size="lg" fullWidth onClick={fetchNext}>
                    Next Question
                    <ChevronRight className="w-5 h-5" />
                  </Button>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
