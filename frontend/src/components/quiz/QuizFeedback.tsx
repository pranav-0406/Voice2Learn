/**
 * QuizFeedback — M05 Adaptive Quiz & Assessment Engine
 *
 * Renders celebratory or constructive pedagogical feedback after an answer attempt:
 *  - Correct answer celebration with point award animation
 *  - Explanatory concept recap with spoken audio guidance
 *  - Next question button with voice shortcut integration
 */

import { useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Sparkles,
  Trophy,
  Volume2,
} from 'lucide-react'
import { speakText, speechSupported } from '../../speech'
import type { AnswerResult } from '../../types'

interface QuizFeedbackProps {
  feedback: AnswerResult
  onNext: () => void
}

export function QuizFeedback({ feedback, onNext }: QuizFeedbackProps) {
  const isCorrect = feedback.correct
  const explanation = feedback.explanation || feedback.message

  // Auto-narrate feedback outcome & explanation once when mounted
  useEffect(() => {
    if (!speechSupported()) return

    if (isCorrect) {
      speakText(`Correct! You earned ${feedback.points_awarded} points.`)
    } else {
      const speech = explanation
        ? `Not quite. ${explanation}`
        : 'Not quite. Review the lesson and keep practicing!'
      speakText(speech)
    }
  }, [isCorrect, explanation, feedback.points_awarded])

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96, y: 12 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={`quiz-feedback-card ${isCorrect ? 'correct' : 'incorrect'}`}
      role="status"
      aria-live="polite"
    >
      {/* ── Status Banner ── */}
      <div className="quiz-feedback-card__banner">
        <div className="quiz-feedback-card__icon-wrapper" aria-hidden="true">
          {isCorrect ? (
            <CheckCircle2 size={32} className="feedback-icon correct" />
          ) : (
            <AlertCircle size={32} className="feedback-icon incorrect" />
          )}
        </div>

        <div className="quiz-feedback-card__titles">
          <p className="quiz-feedback-card__eyebrow">
            {isCorrect ? 'SUPERB JOB!' : 'KEEP GOING!'}
          </p>
          <h2 className="quiz-feedback-card__headline">
            {isCorrect ? 'You got it right!' : 'Good try — here is the concept:'}
          </h2>
        </div>

        {isCorrect && feedback.points_awarded > 0 && (
          <div className="quiz-feedback-card__points-badge" aria-label={`+${feedback.points_awarded} points`}>
            <Sparkles size={16} aria-hidden="true" />
            <span>+{feedback.points_awarded} pts</span>
          </div>
        )}
      </div>

      {/* ── Explanation Box ── */}
      <div className="quiz-feedback-card__explanation-box">
        <div className="explanation-header">
          <span className="explanation-label">
            {isCorrect ? 'Key Takeaway' : 'Why this is the answer:'}
          </span>
          {speechSupported() && explanation && (
            <button
              type="button"
              className="explanation-speak-btn"
              onClick={() => speakText(explanation)}
              title="Listen to explanation"
              aria-label="Listen to explanation"
            >
              <Volume2 size={16} aria-hidden="true" />
              <span>Listen</span>
            </button>
          )}
        </div>
        <p className="explanation-text">{explanation}</p>
        {!isCorrect && feedback.correct_answer && (
          <div className="correct-answer-pill">
            <strong>Correct answer:</strong> {feedback.correct_answer}
          </div>
        )}
      </div>

      {/* ── Ability / Difficulty Rating Status ── */}
      <div className="quiz-feedback-card__rating-strip">
        <div className="rating-item">
          <Trophy size={14} aria-hidden="true" />
          <span>Skill rating: <strong>{Math.round(feedback.ability)}</strong></span>
        </div>
        <div className="rating-item">
          <span>Target band: <strong className="capitalize">{feedback.target_difficulty}</strong></span>
        </div>
      </div>

      {/* ── Next Question Action ── */}
      <div className="quiz-feedback-card__actions">
        <button
          type="button"
          className="button primary full-width quiz-next-btn"
          id="btn-quiz-next-question"
          onClick={onNext}
          autoFocus
        >
          <span>Next question</span>
          <ArrowRight size={18} aria-hidden="true" />
        </button>
      </div>
    </motion.div>
  )
}
