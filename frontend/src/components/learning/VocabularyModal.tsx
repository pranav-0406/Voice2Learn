/**
 * VocabularyModal — M04 Learning Delivery
 *
 * Accessible inline modal that shows the definition of a vocabulary term
 * and uses TTS to read it aloud. Opened via:
 *  - Click on a highlighted vocabulary word inside the concept card
 *  - Voice command: "define <word>"
 */

import { useEffect, useRef } from 'react'
import { X, Volume2 } from 'lucide-react'
import { speakText, speechSupported } from '../../speech'

export interface VocabEntry {
  term: string
  definition: string
}

interface VocabularyModalProps {
  entry: VocabEntry
  accentColor?: string
  onClose: () => void
}

export function VocabularyModal({ entry, accentColor = '#8B5CF6', onClose }: VocabularyModalProps) {
  const closeRef = useRef<HTMLButtonElement>(null)

  // Trap focus & auto-read on open
  useEffect(() => {
    closeRef.current?.focus()
    if (speechSupported()) {
      speakText(`${entry.term}. ${entry.definition}`)
    }
    return () => {}
  }, [entry])

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div
      className="vocab-modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="vocab-modal-title"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div
        className="vocab-modal"
        style={{ '--vocab-accent': accentColor } as React.CSSProperties}
      >
        {/* Header */}
        <div className="vocab-modal__header">
          <span className="vocab-modal__tag">VOCABULARY</span>
          <button
            ref={closeRef}
            type="button"
            className="vocab-modal__close"
            aria-label="Close vocabulary card"
            onClick={onClose}
            id="btn-vocab-close"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        {/* Term */}
        <h2 id="vocab-modal-title" className="vocab-modal__term">
          {entry.term}
        </h2>

        {/* Definition */}
        <p className="vocab-modal__definition">{entry.definition}</p>

        {/* Listen button */}
        {speechSupported() && (
          <button
            type="button"
            className="vocab-modal__listen"
            onClick={() => speakText(`${entry.term}. ${entry.definition}`)}
            id="btn-vocab-listen"
          >
            <Volume2 size={15} aria-hidden="true" />
            Hear pronunciation
          </button>
        )}
      </div>
    </div>
  )
}
