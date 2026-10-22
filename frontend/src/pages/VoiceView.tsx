import { useEffect, useState, type FormEvent } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Keyboard, Mic, Pause, Play, RotateCcw, Volume2 } from 'lucide-react'
import {
  Button,
  Card,
  Notice,
  Page,
  Spinner,
} from '../components/ui'
import { interpretVoice } from '../api'
import {
  pauseSpeaking,
  resumeSpeaking,
  speakText,
  stopSpeaking,
  type SpeechPlaybackState,
} from '../speech'
import type { Interpretation } from '../types'

export function VoiceView() {
  const [typed, setTyped] = useState('')
  const [typedResult, setTypedResult] = useState<{
    text: string
    interpretation: Interpretation
  } | null>(null)
  const [pending, setPending] = useState(false)
  const [typedError, setTypedError] = useState('')
  const [speechState, setSpeechState] = useState<SpeechPlaybackState>('idle')

  const result = typedResult

  useEffect(() => {
    const handler = (event: Event) => {
      const nextState = (event as CustomEvent<{ state: SpeechPlaybackState }>).detail?.state
      if (nextState) setSpeechState(nextState)
    }
    window.addEventListener('tts-speaking-change', handler)
    return () => window.removeEventListener('tts-speaking-change', handler)
  }, [])

  useEffect(() => () => stopSpeaking(), [])

  const submitText = async (event: FormEvent) => {
    event.preventDefault()
    if (!typed.trim()) return
    setPending(true)
    setTypedError('')
    try {
      const interpretation = await interpretVoice(typed.trim())
      stopSpeaking()
      setTypedResult({ text: typed.trim(), interpretation })
    } catch (cause) {
      setTypedError(
        cause instanceof Error ? cause.message : 'Could not process that text request.'
      )
    } finally {
      setPending(false)
    }
  }

  const readTranscript = () => {
    if (!result) return
    const textToRead =
      result.interpretation.answer ||
      result.interpretation.response ||
      result.text
    speakText(textToRead)
  }

  return (
    <Page id="voice-assistant-view">
      <header className="voice-header">
        <p className="eyebrow">VOICE ASSISTANT (ENGLISH)</p>
        <h1>Ask in the way that works for you.</h1>
        <p>Use the persistent voice bar at the bottom, or type your question below.</p>
      </header>

      <div className="voice-layout">
        <Card className="voice-stage" id="voice-stage-card">
          <div className="mic-halo" aria-hidden="true">
            <Mic size={48} />
          </div>
          <p className="voice-status" aria-live="polite">
            Turn on <strong>Voice Control</strong> below to listen continuously from any screen.
          </p>
        </Card>

        <Card className="voice-help" id="voice-help-card">
          <p className="eyebrow">HOW IT WORKS</p>
          <h2>Voice navigation & questions</h2>
          <ol>
            <li>
              <span>1</span>
              Turn on Voice Control in the bottom bar.
            </li>
            <li>
              <span>2</span>
              Speak commands like <em>"Open dashboard"</em>, <em>"Open lesson"</em>, or <em>"Start quiz"</em>.
            </li>
            <li>
              <span>3</span>
              Ask questions like <em>"What is a solid?"</em> or <em>"Explain measurement units"</em>.
            </li>
          </ol>
          <p className="muted">
            Microphone permissions are required for voice features. All interactions are in English.
          </p>
        </Card>
      </div>

      <Card className="text-alternative" id="text-alternative-card">
        <div>
          <Keyboard aria-hidden="true" />
          <div>
            <p className="eyebrow">TEXT ALTERNATIVE</p>
            <h2>Prefer to type your question?</h2>
          </div>
        </div>
        <form onSubmit={submitText}>
          <label className="sr-only" htmlFor="question-input">
            Your question or command in English
          </label>
          <input
            id="question-input"
            value={typed}
            onChange={event => setTyped(event.target.value)}
            placeholder="Type a subject question or command (e.g., What are the states of matter?)"
          />
          <Button type="submit" disabled={pending} id="btn-submit-text-question">
            {pending ? <Spinner label="Processing..." /> : 'Send'}
          </Button>
        </form>
        {typedError && <Notice>{typedError}</Notice>}
      </Card>

      <AnimatePresence>
        {result && (
          <motion.section
            className="voice-result"
            id="voice-result-section"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <Card>
              <p className="eyebrow">YOU ASKED</p>
              <blockquote>“{result.text}”</blockquote>
              <div className="action-row">
                <Button
                  variant="secondary"
                  onClick={readTranscript}
                  id="btn-read-voice-result"
                >
                  <Volume2 size={17} aria-hidden="true" />
                  Read aloud
                </Button>
                {speechState !== 'idle' && (
                  <Button
                    variant="quiet"
                    onClick={speechState === 'paused' ? resumeSpeaking : pauseSpeaking}
                    aria-label={speechState === 'paused' ? 'Resume speaking' : 'Stop speaking'}
                  >
                    {speechState === 'paused' ? <Play size={17} aria-hidden="true" /> : <Pause size={17} aria-hidden="true" />}
                    {speechState === 'paused' ? 'Resume speaking' : 'Stop speaking'}
                  </Button>
                )}
                <Button
                  variant="quiet"
                  onClick={() => {
                    stopSpeaking()
                    setTypedResult(null)
                    setTyped('')
                  }}
                >
                  <RotateCcw size={17} aria-hidden="true" />
                  Ask another
                </Button>
              </div>
            </Card>

            <Card className="interpretation">
              <p className="eyebrow">ASSISTANT RESPONSE</p>
              <span className="status-pill">
                {result.interpretation.intent.replace('_', ' ')}
              </span>
              {result.interpretation.answer ? (
                <p>{result.interpretation.answer}</p>
              ) : result.interpretation.response ? (
                <p>{result.interpretation.response}</p>
              ) : (
                <p>
                  {result.interpretation.intent === 'question'
                    ? 'Your question was understood and processed.'
                    : 'Your voice request was recognised.'}
                </p>
              )}
            </Card>
          </motion.section>
        )}
      </AnimatePresence>
    </Page>
  )
}
