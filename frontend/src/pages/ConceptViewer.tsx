/**
 * ConceptViewer — M04 Learning Delivery page
 *
 * The full-screen learning experience for a single curriculum concept.
 * Route: /concept/:conceptId
 *
 * Layout:
 *  ┌──────────────────────────────────────────────────────┐
 *  │  Navbar                                              │
 *  ├──────────────────────────────────────────────────────┤
 *  │  ConceptCard (main)  │  ChapterContents (sidebar)   │
 *  ├──────────────────────────────────────────────────────┤
 *  │  AudioNarrationBar (sticky bottom)                   │
 *  └──────────────────────────────────────────────────────┘
 *
 * Voice commands handled here and delegated via window events:
 *   "read lesson"    → READ_LESSON
 *   "next idea"      → NEXT_CONCEPT
 *   "previous idea"  → PREV_CONCEPT
 *   "repeat point"   → REPEAT_POINT
 *   "stop"           → STOP_SPEAKING
 */

import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { ArrowLeft, BookOpen, Trophy } from 'lucide-react'
import { Page, PageError } from '../components/ui'
import { ConceptCard } from '../components/learning/ConceptCard'
import { ChapterContents } from '../components/learning/ChapterContents'
import { AudioNarrationBar } from '../components/learning/AudioNarrationBar'
import { fetchConceptLesson, saveActivePosition } from '../api'
import { stopSpeaking } from '../speech'
import type { ConceptLesson, NarrationState } from '../types'

// ── Loading skeleton ──────────────────────────────────────────────────────────
function ConceptSkeleton() {
  return (
    <div className="concept-viewer__skeleton" aria-busy="true" aria-label="Loading concept">
      <div className="skeleton concept-viewer__skeleton-header" />
      <div className="skeleton concept-viewer__skeleton-block" />
      <div className="skeleton concept-viewer__skeleton-block" style={{ width: '80%' }} />
      <div className="skeleton concept-viewer__skeleton-block" style={{ width: '65%' }} />
    </div>
  )
}

// ── ConceptViewer ─────────────────────────────────────────────────────────────

export function ConceptViewer() {
  const { conceptId } = useParams<{ conceptId: string }>()
  const navigate = useNavigate()

  const [concept, setConcept] = useState<ConceptLesson | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [narrationState, setNarrationState] = useState<NarrationState>('idle')
  const [activePointIndex, setActivePointIndex] = useState(-1)
  const [completedIds, setCompletedIds] = useState<Set<string>>(new Set())

  // Load concept from API
  const loadConcept = useCallback((id: string) => {
    setLoading(true)
    setError('')
    fetchConceptLesson(id)
      .then(data => {
        setConcept(data)
        setLoading(false)
        // Mark previous concept as completed
        setCompletedIds(prev => {
          const next = new Set(prev)
          if (id !== conceptId) next.add(conceptId ?? '')
          return next
        })
        // Persist active learning position to SQLite
        const learnerRaw = localStorage.getItem('v2l-learner')
        if (learnerRaw) {
          try {
            const l = JSON.parse(learnerRaw)
            if (l?.id) {
              void saveActivePosition(l.id, data.subject_id, data.chapter_id, data.id)
            }
          } catch {}
        }
      })
      .catch(err => {
        setError(err instanceof Error ? err.message : 'Concept not found.')
        setLoading(false)
      })
  }, [conceptId])

  useEffect(() => {
    if (conceptId) loadConcept(conceptId)
  }, [conceptId])

  // Navigate to another concept by ID (update URL)
  function navigateToConcept(id: string) {
    stopSpeaking()
    setNarrationState('idle')
    setActivePointIndex(-1)
    navigate(`/concept/${encodeURIComponent(id)}`, { replace: false })
    loadConcept(id)
  }

  // Voice command router for this screen
  useEffect(() => {
    if (!concept) return
    const handler = (e: Event) => {
      const action = (e as CustomEvent<{ action: string }>).detail?.action
      if (action === 'NEXT_CONCEPT' && concept.next_concept) {
        navigateToConcept(concept.next_concept.id)
      } else if (action === 'PREV_CONCEPT' && concept.prev_concept) {
        navigateToConcept(concept.prev_concept.id)
      }
    }
    window.addEventListener('voice-command', handler)
    return () => window.removeEventListener('voice-command', handler)
  }, [concept])

  // Register voice intents supported on this screen
  useEffect(() => {
    window.dispatchEvent(
      new CustomEvent('voice-context', {
        detail: {
          screen: 'concept-viewer',
          lesson_topic: concept?.title ?? 'concept',
          supported_commands: ['read lesson', 'next idea', 'previous idea', 'repeat point', 'stop'],
        },
      })
    )
  }, [concept?.id])

  if (error) return <PageError message={error} />

  return (
    <Page id="concept-viewer-page">
      {/* ── Top bar ──────────────────────────────────────────────────────── */}
      <div className="concept-viewer__topbar">
        <button
          type="button"
          className="concept-viewer__back"
          onClick={() => navigate(-1)}
          id="btn-concept-back"
          aria-label="Back to chapter"
        >
          <ArrowLeft size={18} aria-hidden="true" />
          <span>Back</span>
        </button>

        {concept && (
          <div className="concept-viewer__topbar-meta">
            <BookOpen size={15} aria-hidden="true" />
            <span>{concept.subject_name} · Term {concept.term}, Chapter {concept.chapter_number}</span>
          </div>
        )}

        {concept && completedIds.size > 0 && (
          <div className="concept-viewer__progress-badge" aria-label={`${completedIds.size} concepts completed`}>
            <Trophy size={14} aria-hidden="true" />
            <span>{completedIds.size} done</span>
          </div>
        )}
      </div>

      {/* ── Main layout ──────────────────────────────────────────────────── */}
      <div className="concept-viewer__layout">
        {/* Card area */}
        <div className="concept-viewer__main">
          <AnimatePresence mode="wait">
            {loading ? (
              <ConceptSkeleton key="skeleton" />
            ) : concept ? (
              <ConceptCard
                key={concept.id}
                concept={concept}
                narrationState={narrationState}
                activePointIndex={activePointIndex}
                onNavigate={navigateToConcept}
              />
            ) : null}
          </AnimatePresence>
        </div>

        {/* Sidebar TOC */}
        {concept && (
          <aside className="concept-viewer__sidebar" aria-label="Chapter table of contents">
            <ChapterContents
              chapterTitle={concept.chapter_title}
              concepts={concept.all_concepts}
              activeConceptId={concept.id}
              onSelect={navigateToConcept}
              completedIds={completedIds}
            />

            {/* Voice hint card */}
            <div className="concept-viewer__voice-hints">
              <p className="concept-viewer__voice-hints-title">🎙️ Voice Commands</p>
              <ul>
                <li><kbd>read lesson</kbd> — narrate this concept</li>
                <li><kbd>next idea</kbd> — go to next concept</li>
                <li><kbd>previous idea</kbd> — go back</li>
                <li><kbd>repeat point</kbd> — replay current key point</li>
                <li><kbd>stop</kbd> — pause narration</li>
              </ul>
            </div>
          </aside>
        )}
      </div>

      {/* ── Audio narration bar ──────────────────────────────────────────── */}
      {concept && !loading && (
        <AudioNarrationBar
          title={concept.title}
          summary={concept.summary}
          keyPoints={concept.key_points}
          accentColor={concept.subject_accent}
        />
      )}
    </Page>
  )
}
