/**
 * Voice2Learn Single-Utterance Audio Capture Engine
 * Encapsulates getUserMedia, MediaRecorder, and Web Audio RMS VAD.
 * Enforces single acquisition per session, 1800ms trailing silence, and 15s max ceiling.
 */

export const DEFAULT_SPEECH_RMS_THRESHOLD = 0.008
export const MAX_RECORDING_DURATION_MS = 15000 // 15 seconds hard maximum
export const TRAILING_SILENCE_MS = 1800 // 1800ms trailing silence for accessibility
export const MIN_UTTERANCE_MS = 500 // 500ms minimum utterance
export const MIN_AUDIO_BLOB_BYTES = 4096 // 4KB minimum blob size before upload

export function getStoredMicThreshold(): number {
  if (typeof window === 'undefined') return DEFAULT_SPEECH_RMS_THRESHOLD
  const val = parseFloat(localStorage.getItem('v2l-mic-threshold') || '')
  return isNaN(val) || val <= 0 ? DEFAULT_SPEECH_RMS_THRESHOLD : val
}

export function setStoredMicThreshold(value: number): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('v2l-mic-threshold', value.toFixed(4))
    window.dispatchEvent(
      new CustomEvent('mic-threshold-change', { detail: { threshold: value } })
    )
  }
}

export function getSupportedMimeType(): string {
  if (typeof window === 'undefined' || typeof MediaRecorder === 'undefined') return ''
  const types = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/mp4',
    'audio/wav',
  ]
  for (const t of types) {
    if (MediaRecorder.isTypeSupported(t)) return t
  }
  return ''
}

export interface AudioCaptureCallbacks {
  onSpeechStart?: (sessionId: string) => void
  onSpeechEnd?: (sessionId: string) => void
  onAudioData: (audioBlob: Blob, sessionId: string) => void
  onError: (error: Error, sessionId: string) => void
  onRmsLevel?: (rms: number, sessionId: string) => void
}

export class AudioCapture {
  private mediaStream: MediaStream | null = null
  private mediaRecorder: MediaRecorder | null = null
  private audioContext: AudioContext | null = null
  private analyser: AnalyserNode | null = null
  private vadFrameId: number | null = null
  private maxDurationTimer: number | null = null
  private chunks: Blob[] = []
  private activeSessionId: string = ''
  private isAborted: boolean = false
  private callbacks: AudioCaptureCallbacks | null = null
  private mimeType: string = ''

  /**
   * Check if browser environment supports microphone recording.
   */
  public static isSupported(): boolean {
    return (
      typeof window !== 'undefined' &&
      !!navigator.mediaDevices?.getUserMedia &&
      typeof MediaRecorder !== 'undefined'
    )
  }

  /**
   * Start recording a single speech utterance for the given session.
   */
  public async start(sessionId: string, callbacks: AudioCaptureCallbacks): Promise<void> {
    if (!AudioCapture.isSupported()) {
      const err = new Error('Audio recording is not supported in this browser environment.')
      callbacks.onError(err, sessionId)
      return
    }

    // Release any previous session resources completely
    this.abort()

    this.activeSessionId = sessionId
    this.callbacks = callbacks
    this.isAborted = false
    this.chunks = []
    this.mimeType = getSupportedMimeType()

    try {
      // 1. Single getUserMedia acquisition with hardware acoustic enhancements
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      })

      // If aborted during async getUserMedia call, release stream immediately
      if (this.isAborted || this.activeSessionId !== sessionId) {
        stream.getTracks().forEach((t) => t.stop())
        return
      }

      this.mediaStream = stream

      // 2. MediaRecorder setup
      const recorderOptions: MediaRecorderOptions = this.mimeType ? { mimeType: this.mimeType } : {}
      const recorder = new MediaRecorder(stream, recorderOptions)
      this.mediaRecorder = recorder

      recorder.ondataavailable = (event: BlobEvent) => {
        if (event.data && event.data.size > 0) {
          this.chunks.push(event.data)
        }
      }

      recorder.onstop = () => {
        const finalSession = this.activeSessionId
        const isCleanExit = !this.isAborted && finalSession === sessionId
        const recordedChunks = this.chunks
        this.cleanup()

        if (isCleanExit && recordedChunks.length > 0) {
          const blob = new Blob(recordedChunks, { type: this.mimeType || 'audio/webm' })
          if (blob.size < MIN_AUDIO_BLOB_BYTES) {
            console.log(
              `[AudioCapture] Blob size (${blob.size} bytes) < min ${MIN_AUDIO_BLOB_BYTES} bytes. Discarding silence snippet.`
            )
          } else {
            this.callbacks?.onAudioData(blob, finalSession)
          }
        }
      }

      // 3. Web Audio RMS VAD Setup
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
      if (AudioCtx) {
        const ctx = new AudioCtx()
        this.audioContext = ctx
        const source = ctx.createMediaStreamSource(stream)
        const analyser = ctx.createAnalyser()
        analyser.fftSize = 512
        source.connect(analyser)
        this.analyser = analyser

        if (ctx.state === 'suspended') {
          void ctx.resume()
        }

        this.startVadMonitoring(sessionId)
      }

      // Start recording
      recorder.start()

      // 4. Hard ceiling timer: 15 seconds
      this.maxDurationTimer = window.setTimeout(() => {
        console.log(`[AudioCapture] 15s max ceiling reached for session ${sessionId}. Stopping capture.`)
        this.stop()
      }, MAX_RECORDING_DURATION_MS)
    } catch (err) {
      this.cleanup()
      const error = err instanceof Error ? err : new Error(String(err))
      this.callbacks?.onError(error, sessionId)
    }
  }

  /**
   * Monitor audio frames via AnalyserNode RMS calculation.
   */
  private startVadMonitoring(sessionId: string): void {
    if (!this.analyser) return

    const analyser = this.analyser
    const samples = new Float32Array(analyser.fftSize)
    const startTime = performance.now()
    const storedThreshold = getStoredMicThreshold()

    let heardSpeech = false
    let silenceStart: number | null = null
    let ambientRmsSum = 0
    let ambientSampleCount = 0
    let dynamicThreshold = storedThreshold

    const checkFrame = () => {
      if (
        this.isAborted ||
        this.activeSessionId !== sessionId ||
        !this.mediaRecorder ||
        this.mediaRecorder.state !== 'recording'
      ) {
        return
      }

      analyser.getFloatTimeDomainData(samples)
      let sum = 0
      for (let i = 0; i < samples.length; i++) {
        sum += samples[i] * samples[i]
      }
      const rms = Math.sqrt(sum / samples.length)
      const elapsed = performance.now() - startTime

      this.callbacks?.onRmsLevel?.(rms, sessionId)

      // Sample first 200ms of ambient noise floor to adapt threshold gently
      if (elapsed < 200) {
        ambientRmsSum += rms
        ambientSampleCount++
        if (ambientSampleCount > 4) {
          const avgAmbient = ambientRmsSum / ambientSampleCount
          dynamicThreshold = Math.min(0.016, Math.max(storedThreshold, avgAmbient * 1.3))
        }
      }

      if (rms >= dynamicThreshold) {
        if (!heardSpeech) {
          heardSpeech = true
          this.callbacks?.onSpeechStart?.(sessionId)
        }
        silenceStart = null
      } else if (heardSpeech && elapsed >= MIN_UTTERANCE_MS) {
        if (silenceStart === null) {
          silenceStart = performance.now()
        } else if (performance.now() - silenceStart >= TRAILING_SILENCE_MS) {
          // Trailing silence threshold met -> utterance complete
          this.callbacks?.onSpeechEnd?.(sessionId)
          this.stop()
          return
        }
      }

      this.vadFrameId = window.requestAnimationFrame(checkFrame)
    }

    this.vadFrameId = window.requestAnimationFrame(checkFrame)
  }

  /**
   * Stop recording cleanly and process the captured audio blob.
   */
  public stop(): void {
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      try {
        this.mediaRecorder.stop()
      } catch (err) {
        console.warn('[AudioCapture] Error stopping MediaRecorder:', err)
      }
    }
  }

  /**
   * Abort recording immediately, discarding any captured audio and releasing all hardware streams.
   */
  public abort(): void {
    this.isAborted = true
    this.cleanup()
  }

  /**
   * Clean up and release all microphone streams, AudioContexts, and timers.
   */
  private cleanup(): void {
    if (this.maxDurationTimer !== null) {
      window.clearTimeout(this.maxDurationTimer)
      this.maxDurationTimer = null
    }

    if (this.vadFrameId !== null) {
      window.cancelAnimationFrame(this.vadFrameId)
      this.vadFrameId = null
    }

    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      try {
        this.mediaRecorder.stop()
      } catch {
        // Ignore stop error during forced cleanup
      }
    }
    this.mediaRecorder = null

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => {
        try {
          track.stop()
        } catch {
          // Ignore track stop error
        }
      })
      this.mediaStream = null
    }

    if (this.audioContext && this.audioContext.state !== 'closed') {
      try {
        void this.audioContext.close()
      } catch {
        // Ignore context close error
      }
    }
    this.audioContext = null
    this.analyser = null
  }
}
