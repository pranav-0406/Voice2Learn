/**
 * AudioNarrationBar — M04 Learning Delivery
 *
 * A persistent bottom bar that controls TTS narration for a concept.
 * Features:
 *  - Play / Pause / Stop controls
 *  - Progress indicator showing which key point is being narrated
 *  - Voice command integration (READ_LESSON, REPEAT, STOP_SPEAKING)
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { Mic, Pause, Play, Volume2 } from 'lucide-react'
import {
  pauseSpeaking,
  resumeSpeaking,
  speakText,
  speechSupported,
  stopSpeaking,
  type SpeechPlaybackState,
} from '../../speech'
import type { NarrationState } from '../../types'

interface AudioNarrationBarProps {
  title: string
  summary: string
  keyPoints: string[]
  accentColor?: string
}

export function AudioNarrationBar({
  title,
  summary,
  keyPoints,
  accentColor = '#8B5CF6',
}: AudioNarrationBarProps) {
  const [state, setState] = useState<NarrationState>('idle')
  const [playbackState, setPlaybackState] = useState<SpeechPlaybackState>('idle')
  const [pointIndex, setPointIndex] = useState<number>(-1)
  const cancelRef = useRef(false)
  const supported = speechSupported()

  // Narrate the full concept sequentially: summary → each key point
  const narrate = useCallback(
    (startFrom = -1) => {
      if (!supported) return
      cancelRef.current = false
      setState('speaking')

      const segments = [summary, ...keyPoints]
      let idx = startFrom

      function playNext() {
        if (cancelRef.current) return
        idx++
        if (idx >= segments.length) {
          setState('idle')
          setPointIndex(-1)
          return
        }
        setPointIndex(idx - 1) // -1 = summary, 0+ = key point index
        speakText(segments[idx], playNext)
      }

      playNext()
    },
    [summary, keyPoints, supported]
  )

  function handleStop() {
    cancelRef.current = true
    stopSpeaking()
    setState('idle')
    setPointIndex(-1)
  }

  function handlePlaybackToggle() {
    if (playbackState === 'speaking') pauseSpeaking()
    else if (playbackState === 'paused') resumeSpeaking()
    else narrate()
  }

  // Voice command listeners
  useEffect(() => {
    const playbackHandler = (event: Event) => {
      const nextState = (event as CustomEvent<{ state: SpeechPlaybackState }>).detail?.state
      if (nextState) setPlaybackState(nextState)
    }
    window.addEventListener('tts-speaking-change', playbackHandler)
    const handler = (e: Event) => {
      const action = (e as CustomEvent<{ action: string }>).detail.action
      if (action === 'READ_LESSON' || action === 'REPEAT') {
        handleStop()
        setTimeout(() => narrate(), 100)
      } else if (action === 'STOP_SPEAKING') {
        handleStop()
      }
    }
    window.addEventListener('voice-command', handler)
    return () => {
      window.removeEventListener('tts-speaking-change', playbackHandler)
      window.removeEventListener('voice-command', handler)
    }
  }, [narrate])

  // Stop on unmount
  useEffect(() => () => { cancelRef.current = true; stopSpeaking() }, [])

  if (!supported) return null

  const isActive = state === 'speaking' || playbackState === 'paused'
  const totalSegments = 1 + keyPoints.length // summary + key points
  const currentSegment = pointIndex + 1 // 0 = summary, 1+ = key point n

  return (
    <div
      className="narration-bar"
      role="region"
      aria-label="Audio narration controls"
      style={{ '--narration-accent': accentColor } as React.CSSProperties}
    >
      <div className="narration-bar__info">
        <Volume2 size={18} aria-hidden="true" className="narration-bar__icon" />
        <span className="narration-bar__label">
          {isActive
            ? pointIndex < 0
              ? `Narrating: ${title}`
              : `Key Point ${pointIndex + 1} of ${keyPoints.length}`
            : 'Listen to this concept'}
        </span>
        {isActive && (
          <span className="narration-bar__progress" aria-live="polite" aria-atomic="true">
            <span
              className="narration-bar__pip-track"
              aria-label={`Segment ${currentSegment} of ${totalSegments}`}
            >
              {Array.from({ length: totalSegments }).map((_, i) => (
                <span
                  key={i}
                  className={`narration-bar__pip ${i === currentSegment ? 'narration-bar__pip--active' : i < currentSegment ? 'narration-bar__pip--done' : ''}`}
                />
              ))}
            </span>
          </span>
        )}
      </div>

      <div className="narration-bar__controls">
        {isActive ? (
          <button
            type="button"
            className="narration-btn narration-btn--stop"
            onClick={handlePlaybackToggle}
            aria-label={playbackState === 'paused' ? 'Resume speaking' : 'Stop speaking'}
            id="btn-narration-playback"
          >
            {playbackState === 'paused' ? <Play size={16} aria-hidden="true" /> : <Pause size={16} aria-hidden="true" />}
            <span>{playbackState === 'paused' ? 'Resume speaking' : 'Stop speaking'}</span>
          </button>
        ) : (
          <button
            type="button"
            className="narration-btn narration-btn--play"
            onClick={handlePlaybackToggle}
            aria-label="Play narration"
            id="btn-narration-play"
          >
            <Play size={16} aria-hidden="true" />
            <span>Listen</span>
          </button>
        )}
        <span className="narration-bar__hint">
          <Mic size={12} aria-hidden="true" />
          Say "read lesson"
        </span>
      </div>
    </div>
  )
}
