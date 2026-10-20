/**
 * ConceptCard — M04 Learning Delivery
 *
 * Renders a single curriculum concept as a rich, animated card with:
 *  - Gradient concept header with subject accent color
 *  - Summary block with sparkle decoration
 *  - Numbered key points with highlight animation
 *  - Inline vocabulary word highlighting (tap to define)
 *  - Progress pagination (concept N of M)
 *  - Voice command: "next idea" / "previous idea" / "repeat point"
 */

import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  GraduationCap,
  Lightbulb,
  Sparkles,
} from 'lucide-react'
import { speakText } from '../../speech'
import { VocabularyModal } from './VocabularyModal'
import type { ConceptLesson, ConceptNavRef, NarrationState } from '../../types'

// ── Vocabulary extraction ─────────────────────────────────────────────────────
// Simple heuristic: highlight any word that appears in parenthetical
// definitions within the key points, e.g. "osmosis (movement of water)"
function extractVocabulary(keyPoints: string[]): Record<string, string> {
  const vocab: Record<string, string> = {}
  const re = /\b([A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*)\s*\(([^)]{10,})\)/g
  keyPoints.forEach(point => {
    let m: RegExpExecArray | null
    while ((m = re.exec(point)) !== null) {
      vocab[m[1]] = m[2].charAt(0).toUpperCase() + m[2].slice(1)
    }
  })
  return vocab
}

// ── Paragraph with clickable vocab terms ──────────────────────────────────────
function RichText({
  text,
  vocab,
  onVocabClick,
}: {
  text: string
  vocab: Record<string, string>
  onVocabClick: (term: string) => void
}) {
  if (Object.keys(vocab).length === 0) return <span>{text}</span>

  // Build a regex from vocab keys sorted longest-first to avoid partial matches
  const keys = Object.keys(vocab).sort((a, b) => b.length - a.length)
  const pattern = new RegExp(`\\b(${keys.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})\\b`, 'g')

  const parts: React.ReactNode[] = []
  let last = 0
  let match: RegExpExecArray | null
  let idx = 0

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > last) {
      parts.push(<span key={`t-${idx++}`}>{text.slice(last, match.index)}</span>)
    }
    const term = match[0]
    parts.push(
      <button
        key={`v-${idx++}`}
        type="button"
        className="vocab-term"
        onClick={() => onVocabClick(term)}
        aria-label={`Define: ${term}`}
        id={`vocab-${term.toLowerCase().replace(/\s+/g, '-')}`}
      >
        {term}
      </button>
    )
    last = match.index + match[0].length
  }
  if (last < text.length) parts.push(<span key={`t-${idx}`}>{text.slice(last)}</span>)

  return <>{parts}</>
}

// ── ConceptCard ───────────────────────────────────────────────────────────────

interface ConceptCardProps {
  concept: ConceptLesson
  narrationState: NarrationState
  activePointIndex: number
  onNavigate: (conceptId: string) => void
}

export function ConceptCard({
  concept,
  narrationState,
  activePointIndex,
  onNavigate,
}: ConceptCardProps) {
  const [openVocab, setOpenVocab] = useState<{ term: string; definition: string } | null>(null)
  const vocab = extractVocabulary(concept.key_points)
  const cardRef = useRef<HTMLDivElement>(null)

  function navigate(ref: ConceptNavRef | null) {
    if (!ref) return
    onNavigate(ref.id)
  }

  // Voice command: "next idea", "previous idea", "repeat point"
  useEffect(() => {
    const handler = (e: Event) => {
      const action = (e as CustomEvent<{ action: string }>).detail.action
      if (action === 'NEXT_CONCEPT') navigate(concept.next_concept)
      else if (action === 'PREV_CONCEPT') navigate(concept.prev_concept)
      else if (action === 'REPEAT_POINT') {
        const idx = activePointIndex >= 0 ? activePointIndex : 0
        if (concept.key_points[idx]) speakText(concept.key_points[idx])
      }
    }
    window.addEventListener('voice-command', handler)
    return () => window.removeEventListener('voice-command', handler)
  }, [concept, activePointIndex])

  // Announce voice context for this concept
  useEffect(() => {
    window.dispatchEvent(
      new CustomEvent('voice-context', {
        detail: { screen: 'concept-viewer', lesson_topic: concept.title },
      })
    )
  }, [concept.id])

  return (
    <motion.div
      ref={cardRef}
      className="concept-card"
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
      style={{ '--concept-accent': concept.subject_accent } as React.CSSProperties}
      role="article"
      aria-label={`Concept: ${concept.title}`}
    >
      {/* ── Subject + chapter breadcrumb ─────────────────────────────── */}
      <div className="concept-card__breadcrumb">
        <GraduationCap size={14} aria-hidden="true" />
        <span>{concept.subject_name}</span>
        <ChevronRight size={12} aria-hidden="true" />
        <span>{concept.chapter_title}</span>
      </div>

      {/* ── Concept Header ────────────────────────────────────────────── */}
      <div className="concept-card__header">
        <div className="concept-card__title-group">
          <div className="concept-card__pill">
            Concept {concept.index + 1} of {concept.total}
          </div>
          <h1 className="concept-card__title">{concept.title}</h1>
        </div>
        <div className="concept-card__orb" aria-hidden="true">
          <Sparkles size={32} />
        </div>
      </div>

      {/* ── Summary ──────────────────────────────────────────────────── */}
      <div
        className={`concept-card__summary ${narrationState === 'speaking' && activePointIndex === -1 ? 'concept-card__summary--active' : ''}`}
        aria-live="polite"
      >
        <Sparkles size={18} className="concept-card__summary-icon" aria-hidden="true" />
        <p>
          <RichText text={concept.summary} vocab={vocab} onVocabClick={(t) => setOpenVocab({ term: t, definition: vocab[t] })} />
        </p>
      </div>

      {/* ── Key Points ───────────────────────────────────────────────── */}
      {concept.key_points.length > 0 && (
        <section className="concept-card__keypoints" aria-label="Key learning points">
          <p className="concept-card__section-label">
            <Lightbulb size={14} aria-hidden="true" />
            KEY POINTS
          </p>
          <ol className="concept-card__point-list">
            {concept.key_points.map((point, i) => (
              <motion.li
                key={i}
                className={`concept-card__point ${narrationState === 'speaking' && activePointIndex === i ? 'concept-card__point--active' : ''}`}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.06 }}
              >
                <span className="concept-card__point-num" aria-hidden="true">{i + 1}</span>
                <p>
                  <RichText text={point} vocab={vocab} onVocabClick={(t) => setOpenVocab({ term: t, definition: vocab[t] })} />
                </p>
              </motion.li>
            ))}
          </ol>
        </section>
      )}

      {/* ── Vocabulary hint ──────────────────────────────────────────── */}
      {Object.keys(vocab).length > 0 && (
        <div className="concept-card__vocab-hint">
          <BookOpen size={13} aria-hidden="true" />
          <span>Tap highlighted words to see definitions</span>
        </div>
      )}

      {/* ── Textbook reference ───────────────────────────────────────── */}
      {concept.textbook_pages && (
        <p className="concept-card__textbook-ref">
          📖 Textbook: {concept.textbook_pages}
        </p>
      )}

      {/* ── Navigation ───────────────────────────────────────────────── */}
      <div className="concept-card__nav">
        <button
          type="button"
          className="concept-nav-btn"
          onClick={() => navigate(concept.prev_concept)}
          disabled={!concept.prev_concept}
          aria-label={concept.prev_concept ? `Previous: ${concept.prev_concept.title}` : 'No previous concept'}
          id="btn-concept-prev"
        >
          <ChevronLeft size={18} aria-hidden="true" />
          <span>{concept.prev_concept ? 'Previous' : ''}</span>
        </button>

        {/* Dot pagination */}
        <div className="concept-card__dots" role="tablist" aria-label="Concept navigation">
          {concept.all_concepts.map((c, i) => (
            <button
              key={c.id}
              type="button"
              role="tab"
              aria-selected={c.id === concept.id}
              aria-label={`Concept ${i + 1}: ${c.title}`}
              className={`concept-card__dot ${c.id === concept.id ? 'concept-card__dot--active' : ''}`}
              onClick={() => onNavigate(c.id)}
              id={`dot-concept-${i}`}
            />
          ))}
        </div>

        <button
          type="button"
          className="concept-nav-btn concept-nav-btn--next"
          onClick={() => navigate(concept.next_concept)}
          disabled={!concept.next_concept}
          aria-label={concept.next_concept ? `Next: ${concept.next_concept.title}` : 'No next concept'}
          id="btn-concept-next"
        >
          <span>{concept.next_concept ? 'Next' : ''}</span>
          <ChevronRight size={18} aria-hidden="true" />
        </button>
      </div>

      {/* ── Vocabulary Modal ─────────────────────────────────────────── */}
      <AnimatePresence>
        {openVocab && (
          <VocabularyModal
            key={openVocab.term}
            entry={openVocab}
            accentColor={concept.subject_accent}
            onClose={() => setOpenVocab(null)}
          />
        )}
      </AnimatePresence>
    </motion.div>
  )
}
