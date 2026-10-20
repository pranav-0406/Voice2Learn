/**
 * QuestionCard — M05 Adaptive Quiz & Assessment Engine
 *
 * Renders an adaptive multiple-choice question with:
 *  - Topic and difficulty band indicator
 *  - High-contrast touch and voice choice cards (A, B, C, D)
 *  - Audio narration for the question prompt
 *  - Interactive "Need a hint?" drawer with voice read support
 *  - Submit confirmation
 */

import { motion } from 'framer-motion'
import { Check, HelpCircle, Lightbulb, Volume2 } from 'lucide-react'
import { speakText, speechSupported } from '../../speech'
import type { Difficulty, Question } from '../../types'

interface QuestionCardProps {
  question: Question
  selectedChoice: string | null
  onSelectChoice: (choice: string) => void
  onSubmit: () => void
  disabled?: boolean
  hintOpen: boolean
  onToggleHint: () => void
}

const OPTION_THEMES = [
  { letter: 'A', bg: 'rgba(79, 70, 229, 0.1)', text: '#4338CA', border: '#4F46E5' },
  { letter: 'B', bg: 'rgba(5, 150, 105, 0.1)', text: '#047857', border: '#059669' },
  { letter: 'C', bg: 'rgba(217, 119, 6, 0.1)', text: '#B45309', border: '#D97706' },
  { letter: 'D', bg: 'rgba(225, 29, 72, 0.1)', text: '#BE123C', border: '#E11D48' },
]

const DIFFICULTY_LABELS: Record<Difficulty, { label: string; cls: string }> = {
  easy: { label: 'Foundation', cls: 'diff-easy' },
  medium: { label: 'Growing', cls: 'diff-medium' },
  hard: { label: 'Advanced', cls: 'diff-hard' },
}

export function QuestionCard({
  question,
  selectedChoice,
  onSelectChoice,
  onSubmit,
  disabled = false,
  hintOpen,
  onToggleHint,
}: QuestionCardProps) {
  const diffInfo = DIFFICULTY_LABELS[question.difficulty] || {
    label: question.difficulty,
    cls: 'diff-medium',
  }

  const hintText = question.hint || `Focus on key principles in ${question.topic}. Think carefully about each choice!`

  return (
    <article className="quiz-card" aria-label={`Question: ${question.prompt}`}>
      {/* ── Question Header ── */}
      <div className="quiz-card__header">
        <div className="quiz-card__meta">
          <span className="quiz-card__topic">{question.topic}</span>
          <span className={`quiz-card__difficulty ${diffInfo.cls}`}>
            {diffInfo.label}
          </span>
        </div>
        <div className="quiz-card__actions">
          <button
            type="button"
            className="quiz-card__audio-btn"
            onClick={() => speakText(question.prompt)}
            aria-label="Read question aloud"
            title="Read question aloud"
            disabled={!speechSupported() || disabled}
          >
            <Volume2 size={18} aria-hidden="true" />
          </button>
        </div>
      </div>

      {/* ── Prompt ── */}
      <h2 className="quiz-card__prompt">{question.prompt}</h2>

      {/* ── Hint Drawer ── */}
      <div className="quiz-card__hint-wrapper">
        <button
          type="button"
          className={`quiz-card__hint-toggle ${hintOpen ? 'open' : ''}`}
          onClick={onToggleHint}
          aria-expanded={hintOpen}
          id="btn-quiz-hint"
        >
          <Lightbulb size={16} aria-hidden="true" />
          <span>{hintOpen ? 'Hide Hint' : 'Need a hint?'}</span>
        </button>

        {hintOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="quiz-card__hint-content"
            role="region"
            aria-label="Question Hint"
          >
            <div className="quiz-card__hint-bubble">
              <HelpCircle size={16} className="hint-icon" aria-hidden="true" />
              <p>{hintText}</p>
              {speechSupported() && (
                <button
                  type="button"
                  className="hint-speak-btn"
                  onClick={() => speakText(hintText)}
                  title="Read hint aloud"
                  aria-label="Read hint aloud"
                >
                  <Volume2 size={14} aria-hidden="true" />
                </button>
              )}
            </div>
          </motion.div>
        )}
      </div>

      {/* ── 4 High-Contrast Choice Cards ── */}
      <div
        className="quiz-card__choices"
        role="group"
        aria-label="Multiple choice options. Say 'Option A', 'B', 'C', or 'D'"
      >
        {question.choices.map((choice, index) => {
          const theme = OPTION_THEMES[index % OPTION_THEMES.length]
          const isSelected = selectedChoice === choice

          return (
            <motion.button
              key={choice}
              type="button"
              id={`quiz-option-${theme.letter}`}
              className={`quiz-choice-btn ${isSelected ? 'selected' : ''}`}
              disabled={disabled}
              onClick={() => onSelectChoice(choice)}
              whileHover={{ scale: disabled ? 1 : 1.015 }}
              whileTap={{ scale: disabled ? 1 : 0.985 }}
              aria-pressed={isSelected}
              style={
                isSelected
                  ? {
                      borderColor: theme.border,
                      boxShadow: `0 0 0 2px ${theme.border}40, 0 6px 18px ${theme.border}20`,
                    }
                  : undefined
              }
            >
              <span
                className="quiz-choice-badge"
                style={{
                  backgroundColor: theme.bg,
                  color: theme.text,
                  borderColor: isSelected ? theme.border : 'transparent',
                }}
                aria-hidden="true"
              >
                {theme.letter}
              </span>
              <span className="quiz-choice-text">{choice}</span>
              {isSelected && (
                <span
                  className="quiz-choice-check"
                  style={{ backgroundColor: theme.border }}
                  aria-hidden="true"
                >
                  <Check size={14} color="#ffffff" strokeWidth={3} />
                </span>
              )}
            </motion.button>
          )
        })}
      </div>

      {/* ── Submit Action ── */}
      <div className="quiz-card__footer">
        <button
          type="button"
          className="button primary full-width quiz-submit-btn"
          id="btn-quiz-submit-choice"
          disabled={!selectedChoice || disabled}
          onClick={onSubmit}
        >
          {selectedChoice ? 'Submit Answer' : 'Select an Option Above'}
        </button>
      </div>
    </article>
  )
}
