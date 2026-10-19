import { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mic, MicOff, Square, RotateCcw, Volume2, VolumeX, Keyboard } from 'lucide-react'
import { useState } from 'react'
import { Button } from '../components/ui/Button'
import { Card, Badge } from '../components/ui/Card'
import { useVoice } from '../hooks/useVoice'
import { useTTS } from '../hooks/useTTS'
import { interpretVoice } from '../services/api'
import type { Learner, VoiceInterpretResponse } from '../types'

interface VoiceInterfaceProps { learner: Learner }

type UiPhase = 'idle' | 'recording' | 'processing' | 'done' | 'error'

const intentLabel: Record<string, string> = {
  command: 'Voice command recognised',
  quiz_answer: 'Quiz answer ready',
  question: 'Question detected — transcribed successfully',
  unknown: 'Input recorded',
}

const intentColor: Record<string, string> = {
  command: 'indigo',
  quiz_answer: 'emerald',
  question: 'violet',
  unknown: 'slate',
}

export default function VoiceInterface({ learner }: VoiceInterfaceProps) {
  const { state, error, result, supported, startRecording, stopRecording, reset } = useVoice(false)
  const { speak, stop, speaking } = useTTS()
  const [textFallback, setTextFallback] = useState(false)
  const [fallbackText, setFallbackText] = useState('')
  const [fallbackResult, setFallbackResult] = useState<VoiceInterpretResponse | null>(null)
  const [fallbackLoading, setFallbackLoading] = useState(false)

  const phase: UiPhase =
    state === 'recording' ? 'recording'
    : state === 'processing' ? 'processing'
    : state === 'done' ? 'done'
    : state === 'error' ? 'error'
    : 'idle'

  // Auto-speak transcription when done
  useEffect(() => {
    if (phase === 'done' && result) {
      speak(`You said: ${result.transcript}`)
    }
  }, [phase, result?.transcript])

  async function handleFallbackSubmit(e: React.FormEvent) {
    e.preventDefault()
    const text = fallbackText.trim()
    if (!text) return
    setFallbackLoading(true)
    try {
      const interp = await interpretVoice(text, false)
      setFallbackResult(interp)
    } catch {
      setFallbackResult(null)
    } finally {
      setFallbackLoading(false)
    }
  }

  const activeInterpretation = result?.interpretation ?? fallbackResult
  const transcript = result?.transcript ?? (fallbackResult ? fallbackText : null)

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-navy-900 tracking-tight mb-1">Ask with Voice</h1>
        <p className="text-sm text-navy-700/50">Speak your Science question and I'll transcribe it for you.</p>
      </div>

      {/* Mic control — the signature element */}
      <div className="flex flex-col items-center py-4">
        <div className="relative flex items-center justify-center mb-6">
          {/* Pulse rings — only while recording */}
          {phase === 'recording' && (
            <>
              <motion.div
                className="absolute w-36 h-36 rounded-full bg-violet-600/15"
                animate={{ scale: [1, 1.25, 1], opacity: [0.5, 0, 0.5] }}
                transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
              />
              <motion.div
                className="absolute w-28 h-28 rounded-full bg-violet-600/20"
                animate={{ scale: [1, 1.18, 1], opacity: [0.7, 0.1, 0.7] }}
                transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut', delay: 0.3 }}
              />
            </>
          )}

          {/* Main mic button */}
          <motion.button
            className={[
              'relative z-10 w-24 h-24 rounded-full flex items-center justify-center shadow-lg transition-colors duration-200',
              'focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-offset-4',
              phase === 'recording'
                ? 'bg-violet-600 text-white focus-visible:ring-violet-400'
                : phase === 'processing'
                ? 'bg-primary-400 text-white cursor-wait focus-visible:ring-primary-400'
                : phase === 'error'
                ? 'bg-rose-500 text-white focus-visible:ring-rose-400'
                : 'bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-500',
            ].join(' ')}
            aria-label={
              phase === 'recording' ? 'Stop recording'
              : phase === 'processing' ? 'Processing…'
              : 'Start recording'
            }
            aria-pressed={phase === 'recording'}
            disabled={phase === 'processing' || !supported}
            onClick={phase === 'recording' ? stopRecording : phase === 'idle' || phase === 'error' ? startRecording : undefined}
            animate={phase === 'idle' ? { scale: [1, 1.03, 1] } : { scale: 1 }}
            transition={phase === 'idle' ? { duration: 3, repeat: Infinity, ease: 'easeInOut' } : undefined}
            whileTap={{ scale: 0.93 }}
          >
            {phase === 'recording' ? (
              <Square className="w-8 h-8 fill-current" />
            ) : phase === 'processing' ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              >
                <Mic className="w-8 h-8" />
              </motion.div>
            ) : phase === 'error' ? (
              <MicOff className="w-8 h-8" />
            ) : (
              <Mic className="w-8 h-8" />
            )}
          </motion.button>
        </div>

        {/* Status label */}
        <AnimatePresence mode="wait">
          <motion.p
            key={phase}
            className="text-sm font-semibold text-navy-700/70 text-center"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.2 }}
          >
            {phase === 'idle' && (supported ? 'Ready to listen' : 'Microphone not supported')}
            {phase === 'recording' && 'Listening… tap to stop'}
            {phase === 'processing' && 'Transcribing…'}
            {phase === 'done' && 'Done'}
            {phase === 'error' && 'Something went wrong'}
          </motion.p>
        </AnimatePresence>

        {/* Not supported message */}
        {!supported && (
          <p className="mt-2 text-xs text-rose-500 text-center max-w-xs">
            Voice recording requires Chrome or Edge on a device with a microphone.
            Use the text input below instead.
          </p>
        )}
      </div>

      {/* Error */}
      {phase === 'error' && error && (
        <Card className="p-4 border-rose-200 bg-rose-50">
          <p className="text-sm text-rose-700 mb-3">{error}</p>
          <Button variant="secondary" size="sm" onClick={reset}>
            <RotateCcw className="w-4 h-4" />
            Try again
          </Button>
        </Card>
      )}

      {/* Transcript + interpretation */}
      <AnimatePresence>
        {transcript && (
          <motion.div
            className="space-y-3"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            {/* Transcript */}
            <Card className="p-5">
              <p className="text-xs font-bold text-navy-700/40 uppercase tracking-wide mb-2">You said</p>
              <p className="text-navy-900 font-medium leading-relaxed">"{transcript}"</p>
            </Card>

            {/* Intent */}
            {activeInterpretation && (
              <Card className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs font-bold text-navy-700/40 uppercase tracking-wide">Recognised as</p>
                  <Badge color={intentColor[activeInterpretation.intent] as never}>
                    {activeInterpretation.intent}
                  </Badge>
                </div>
                <p className="text-sm text-navy-900 mb-3">
                  {intentLabel[activeInterpretation.intent]}
                </p>
                {activeInterpretation.intent === 'question' && (
                  <div className="p-3 rounded-xl bg-amber-50 border border-amber-200">
                    <p className="text-xs text-amber-700 font-medium">
                      Question transcribed. The voice Q&A answer engine is not yet connected to this demo.
                      To get an answer, head to the Lesson or use the Quiz.
                    </p>
                  </div>
                )}
                {activeInterpretation.command && (
                  <p className="text-xs text-primary-600 font-semibold">
                    Command: {activeInterpretation.command}
                  </p>
                )}
              </Card>
            )}

            {/* TTS controls */}
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => speak(transcript)}
                disabled={speaking}
              >
                <Volume2 className="w-4 h-4" />
                Repeat
              </Button>
              {speaking && (
                <Button variant="ghost" size="sm" onClick={stop}>
                  <VolumeX className="w-4 h-4" />
                  Stop speaking
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={() => { reset(); setFallbackResult(null) }}>
                <RotateCcw className="w-4 h-4" />
                Ask again
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Text fallback */}
      <div>
        <button
          className="flex items-center gap-1.5 text-xs text-navy-700/50 hover:text-navy-700 transition-colors duration-150 mb-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 rounded"
          onClick={() => setTextFallback(v => !v)}
        >
          <Keyboard className="w-3.5 h-3.5" />
          {textFallback ? 'Hide text input' : 'Type instead'}
        </button>
        <AnimatePresence>
          {textFallback && (
            <motion.form
              onSubmit={handleFallbackSubmit}
              className="flex gap-2"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
            >
              <input
                type="text"
                value={fallbackText}
                onChange={e => setFallbackText(e.target.value)}
                placeholder="Type your question…"
                className="flex-1 h-11 px-4 rounded-xl border border-base-200 bg-white text-sm text-navy-900 placeholder-navy-700/30 focus:outline-none focus:ring-2 focus:ring-primary-500"
                aria-label="Type your question"
              />
              <Button type="submit" size="md" loading={fallbackLoading}>Send</Button>
            </motion.form>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
