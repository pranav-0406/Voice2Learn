import { useCallback, useEffect, useRef, useState } from 'react'
import { interpretVoice, transcribeAudio, type Interpretation, type VoiceContext } from './api'
import { voiceDiagnostic } from './voiceDiagnostics'

export type VoiceState = 'idle' | 'recording' | 'processing' | 'done' | 'error'
type VoiceResult = { text: string; interpretation: Interpretation; startedAt: number }

const SEGMENT_DURATION_MS = 4500
const RETRY_DELAY_MS = 1200
const SILENCE_DURATION_MS = 650
const MIN_UTTERANCE_MS = 500
const SPEECH_RMS_THRESHOLD = 0.025

function browserSupportsRecording() {
  return typeof window !== 'undefined' && !!navigator.mediaDevices?.getUserMedia && !!window.MediaRecorder
}

export function useVoice(context: VoiceContext = {}) {
  const recorder = useRef<MediaRecorder | null>(null)
  const stream = useRef<MediaStream | null>(null)
  const chunks = useRef<Blob[]>([])
  const loopId = useRef(0)
  const enabledRef = useRef(false)
  const timer = useRef<number | null>(null)
  const processing = useRef(false)
  const recentTurns = useRef<string[]>([])
  const audioContext = useRef<AudioContext | null>(null)
  const vadFrame = useRef<number | null>(null)
  const [enabled, setEnabled] = useState(false)
  const [state, setState] = useState<VoiceState>('idle')
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<VoiceResult | null>(null)
  const supported = browserSupportsRecording()

  const release = useCallback(() => {
    if (timer.current !== null) {
      window.clearTimeout(timer.current)
      timer.current = null
    }
    if (vadFrame.current !== null) {
      window.cancelAnimationFrame(vadFrame.current)
      vadFrame.current = null
    }
    void audioContext.current?.close()
    audioContext.current = null
    stream.current?.getTracks().forEach(track => track.stop())
    stream.current = null
    recorder.current = null
  }, [])

  const stop = useCallback(() => {
    loopId.current += 1
    enabledRef.current = false
    setEnabled(false)
    processing.current = false
    const activeRecorder = recorder.current
    if (activeRecorder?.state === 'recording') activeRecorder.stop()
    release()
    setState('idle')
  }, [release])

  const recordSegment = useCallback(async (id: number) => {
    if (!enabledRef.current || id !== loopId.current || processing.current) return
    if (typeof window !== 'undefined' && window.speechSynthesis?.speaking) {
      timer.current = window.setTimeout(() => void recordSegment(id), 250)
      return
    }

    setError(null)
    setState('recording')
    const recordingStartedAt = voiceDiagnostic('recording-start')
    try {
      const media = await navigator.mediaDevices.getUserMedia({ audio: true })
      if (!enabledRef.current || id !== loopId.current) {
        media.getTracks().forEach(track => track.stop())
        return
      }
      stream.current = media
      chunks.current = []
      const preferredMime = ['audio/webm;codecs=opus', 'audio/webm', 'audio/wav']
        .find(type => MediaRecorder.isTypeSupported(type))
      const next = new MediaRecorder(media, preferredMime ? { mimeType: preferredMime } : undefined)
      recorder.current = next
      next.ondataavailable = event => {
        if (event.data.size) chunks.current.push(event.data)
      }
      next.onstop = () => {
        voiceDiagnostic('recording-stop', recordingStartedAt)
        release()
        if (id !== loopId.current || !enabledRef.current) return
        if (!chunks.current.length) {
          setError('No speech was captured. Retrying…')
          setState('error')
          timer.current = window.setTimeout(() => void recordSegment(id), RETRY_DELAY_MS)
          return
        }
        processing.current = true
        setState('processing')
        const audio = new Blob(chunks.current, { type: next.mimeType || preferredMime || 'audio/webm' })
        chunks.current = []
        void transcribeAudio(audio)
          .then(async transcription => ({
            text: transcription.text,
            interpretation: await interpretVoice(transcription.text, context.active_quiz, {
              ...context,
              recent_turns: recentTurns.current.slice(-4),
            }),
          }))
          .then(transcription => {
            if (id !== loopId.current || !enabledRef.current) return
            setResult({ ...transcription, startedAt: recordingStartedAt })
            const response = transcription.interpretation.response
            recentTurns.current = [
              ...recentTurns.current,
              `learner: ${transcription.text}`,
              ...(response ? [`assistant: ${response}`] : []),
            ].slice(-4)
            setState('done')
          })
          .catch(cause => {
            if (id !== loopId.current || !enabledRef.current) return
            setError(cause instanceof Error ? cause.message : 'Could not transcribe that segment.')
            setState('error')
          })
          .finally(() => {
            processing.current = false
            if (id === loopId.current && enabledRef.current) {
              timer.current = window.setTimeout(() => void recordSegment(id), RETRY_DELAY_MS)
            }
          })
      }
      next.start(100)
      const AudioContextConstructor = window.AudioContext
      if (AudioContextConstructor) {
        const context = new AudioContextConstructor()
        const source = context.createMediaStreamSource(media)
        const analyser = context.createAnalyser()
        analyser.fftSize = 512
        source.connect(analyser)
        void context.resume()
        audioContext.current = context
        const samples = new Float32Array(analyser.fftSize)
        let heardSpeech = false
        let silenceStartedAt: number | null = null
        const monitorSilence = () => {
          if (next.state !== 'recording' || id !== loopId.current || !enabledRef.current) return
          analyser.getFloatTimeDomainData(samples)
          let sum = 0
          for (const sample of samples) sum += sample * sample
          const rms = Math.sqrt(sum / samples.length)
          const elapsed = performance.now() - recordingStartedAt
          if (rms >= SPEECH_RMS_THRESHOLD) {
            heardSpeech = true
            silenceStartedAt = null
          } else if (heardSpeech && elapsed >= MIN_UTTERANCE_MS) {
            silenceStartedAt ??= performance.now()
            if (performance.now() - silenceStartedAt >= SILENCE_DURATION_MS) {
              next.stop()
              return
            }
          }
          vadFrame.current = window.requestAnimationFrame(monitorSilence)
        }
        vadFrame.current = window.requestAnimationFrame(monitorSilence)
      }
      timer.current = window.setTimeout(() => {
        if (next.state === 'recording') next.stop()
      }, SEGMENT_DURATION_MS)
    } catch (cause) {
      release()
      if (id !== loopId.current || !enabledRef.current) return
      setError(cause instanceof DOMException && cause.name === 'NotAllowedError'
        ? 'Microphone permission was denied. Allow access in browser settings, then retry.'
        : 'Microphone could not be started. Check that it is available and try again.')
      setState('error')
    }
  }, [context, release])

  const start = useCallback(async () => {
    if (!supported) {
      setError('Voice recording is unavailable in this browser. You can type your question below.')
      setState('error')
      return
    }
    if (enabled || processing.current) return
    loopId.current += 1
    const id = loopId.current
    enabledRef.current = true
    setEnabled(true)
    setError(null)
    await recordSegment(id)
  }, [enabled, recordSegment, supported])

  const reset = useCallback(() => {
    stop()
    setError(null)
    setResult(null)
  }, [stop])

  useEffect(() => () => {
    loopId.current += 1
    enabledRef.current = false
    const activeRecorder = recorder.current
    if (activeRecorder?.state === 'recording') activeRecorder.stop()
    release()
  }, [release])

  useEffect(() => {
    window.addEventListener('voice-stop', stop)
    return () => window.removeEventListener('voice-stop', stop)
  }, [stop])

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && enabledRef.current) stop()
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [stop])

  return { enabled, state, error, result, supported, start, stop, reset }
}
