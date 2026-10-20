/**
 * ChapterContents — M04 Learning Delivery
 *
 * Collapsible sidebar panel listing all concepts in a chapter, so the student
 * can jump directly to any concept. Highlights the currently active one.
 */

import { useState } from 'react'
import { List, ChevronDown, ChevronUp, CheckCircle2, Circle } from 'lucide-react'
import type { ConceptNavRef } from '../../types'

interface ChapterContentsProps {
  chapterTitle: string
  concepts: ConceptNavRef[]
  activeConceptId: string
  onSelect: (id: string) => void
  completedIds?: Set<string>
}

export function ChapterContents({
  chapterTitle,
  concepts,
  activeConceptId,
  onSelect,
  completedIds = new Set(),
}: ChapterContentsProps) {
  const [open, setOpen] = useState(true)

  return (
    <nav className="chapter-contents" aria-label={`Chapter contents for ${chapterTitle}`}>
      <button
        type="button"
        className="chapter-contents__toggle"
        onClick={() => setOpen(v => !v)}
        aria-expanded={open}
        id="btn-chapter-contents-toggle"
        title={chapterTitle}
      >
        <List size={15} aria-hidden="true" />
        <span>{chapterTitle || 'Chapter Contents'}</span>
        {open ? <ChevronUp size={15} aria-hidden="true" /> : <ChevronDown size={15} aria-hidden="true" />}
      </button>

      {open && (
        <ol className="chapter-contents__list">
          {concepts.map((concept, i) => {
            const isActive = concept.id === activeConceptId
            const isDone = completedIds.has(concept.id)
            return (
              <li key={concept.id}>
                <button
                  type="button"
                  className={`chapter-contents__item ${isActive ? 'chapter-contents__item--active' : ''} ${isDone ? 'chapter-contents__item--done' : ''}`}
                  onClick={() => onSelect(concept.id)}
                  aria-current={isActive ? 'page' : undefined}
                  id={`toc-concept-${i}`}
                >
                  <span className="chapter-contents__num" aria-hidden="true">
                    {isDone ? (
                      <CheckCircle2 size={14} />
                    ) : (
                      <Circle size={14} />
                    )}
                  </span>
                  <span className="chapter-contents__name">{concept.title}</span>
                </button>
              </li>
            )
          })}
        </ol>
      )}
    </nav>
  )
}
