/**
 * MicSensitivityModal — M06 Voice Pipeline Hardening & Acoustic Echo Prevention
 *
 * Interactive audio calibration dialog that allows students/teachers to:
 *  - View a real-time live microphone input level meter
 *  - Perform a 3-second automatic ambient room noise calibration
 *  - Adjust sensitivity threshold presets (Quiet Study, Balanced, Noisy Room)
 *  - Verify the Acoustic Echo Gate status
 */

import { useEffect, useRef, useState } from 'react'
import {
  CheckCircle2,
  Mic,
  ShieldCheck,
  SlidersHorizontal,
  X,
  Zap,
} from 'lucide-react'
import {
  DEFAULT_SPEECH_RMS_THRESHOLD,
  getStoredMicThreshold,
  setStoredMicThreshold,
} from '../../useVoice'

interface MicSensitivityModalProps {
  isOpen: boolean
  onClose: () => void
}

interface PresetOption {
  label: string
  sublabel: string
  value: number
}

const PRESETS: PresetOption[] = [
  { label: 'Quiet Room', sublabel: 'Low background noise, gentle speech', value: 0.014 },
  { label: 'Balanced', sublabel: 'Standard room, moderate distance', value: 0.025 },
  { label: 'Noisy Classroom', sublabel: 'Ceiling fans, AC, background murmur', value: 0.045 },
]

export function MicSensitivityModal({ isOpen, onClose }: MicSensitivityModalProps) {
  const [threshold, setThreshold] = useState<number>(getStoredMicThreshold)
  const [currentLevel, setCurrentLevel] = useState<number>(0)
  const [isCalibrating, setIsCalibrating] = useState(false)
  const [calibProgress, setCalibProgress] = useState(0)
  const [calibSuccess, setCalibSuccess] = useState(false)

  const audioContextRef = useRef<AudioContext | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const animFrameRef = useRef<number | null>(null)

  // Start live audio meter when modal opens
  useEffect(() => {
    if (!isOpen) return

    let cancelled = false
    navigator.mediaDevices
      ?.getUserMedia({ audio: true })
      .then((media) => {
        if (cancelled) {
          media.getTracks().forEach((t) => t.stop())
          return
        }
        streamRef.current = media

        const AudioContextConstructor = window.AudioContext
        if (!AudioContextConstructor) return

        const ctx = new AudioContextConstructor()
        const source = ctx.createMediaStreamSource(media)
        const analyser = ctx.createAnalyser()
        analyser.fftSize = 256
        source.connect(analyser)
        void ctx.resume()
        audioContextRef.current = ctx

        const samples = new Float32Array(analyser.fftSize)

        const loop = () => {
          analyser.getFloatTimeDomainData(samples)
          let sum = 0
          for (const s of samples) sum += s * s
          const rms = Math.sqrt(sum / samples.length)
          setCurrentLevel(rms)
          animFrameRef.current = requestAnimationFrame(loop)
        }
        animFrameRef.current = requestAnimationFrame(loop)
      })
      .catch(() => {
        // Microphone access denied or unavailable in preview
      })

    return () => {
      cancelled = true
      if (animFrameRef.current !== null) {
        cancelAnimationFrame(animFrameRef.current)
        animFrameRef.current = null
      }
      void audioContextRef.current?.close()
      audioContextRef.current = null
      streamRef.current?.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
  }, [isOpen])

  // Run 3-second noise floor calibration
  const runAutoCalibration = () => {
    if (isCalibrating) return
    setIsCalibrating(true)
    setCalibProgress(0)
    setCalibSuccess(false)

    const samplesCollected: number[] = []
    const start = performance.now()
    const durationMs = 3000

    const interval = window.setInterval(() => {
      const elapsed = performance.now() - start
      const progress = Math.min(100, Math.round((elapsed / durationMs) * 100))
      setCalibProgress(progress)
      samplesCollected.push(currentLevel)

      if (elapsed >= durationMs) {
        window.clearInterval(interval)
        setIsCalibrating(false)
        // Average the noise floor and set threshold 2.3x above baseline noise
        const avgNoise =
          samplesCollected.reduce((a, b) => a + b, 0) /
          Math.max(1, samplesCollected.length)
        const calculated = Math.min(
          0.065,
          Math.max(0.012, avgNoise * 2.3 + 0.005)
        )
        setThreshold(calculated)
        setStoredMicThreshold(calculated)
        setCalibSuccess(true)
      }
    }, 100)
  }

  const handleSelectPreset = (value: number) => {
    setThreshold(value)
    setStoredMicThreshold(value)
    setCalibSuccess(false)
  }

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value)
    setThreshold(val)
    setStoredMicThreshold(val)
    setCalibSuccess(false)
  }

  const handleResetDefault = () => {
    setThreshold(DEFAULT_SPEECH_RMS_THRESHOLD)
    setStoredMicThreshold(DEFAULT_SPEECH_RMS_THRESHOLD)
    setCalibSuccess(false)
  }

  if (!isOpen) return null

  const isSpeechTriggered = currentLevel >= threshold
  const meterPercent = Math.min(100, Math.round((currentLevel / 0.08) * 100))
  const thresholdPercent = Math.min(100, Math.round((threshold / 0.08) * 100))

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="mic-calibration-title"
      onClick={onClose}
    >
      <div
        className="modal-card mic-calibration-modal"
        onClick={(e) => e.stopPropagation()}
      >
        {/* ── Modal Header ── */}
        <div className="modal-header">
          <div className="mic-calib-header-icon" aria-hidden="true">
            <SlidersHorizontal size={22} color="#6366f1" />
          </div>
          <div>
            <h2 id="mic-calibration-title" className="modal-title">
              Microphone & Audio Calibration
            </h2>
            <p className="modal-subtitle">
              Configure microphone sensitivity and classroom noise rejection.
            </p>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close calibration modal"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        {/* ── Live Input Visualizer ── */}
        <div className="mic-meter-section">
          <div className="mic-meter-header">
            <span className="meter-label">
              <Mic size={15} aria-hidden="true" />
              <span>Live Mic Level:</span>
            </span>
            <span
              className={`speech-badge ${
                isSpeechTriggered ? 'active' : 'idle'
              }`}
            >
              {isSpeechTriggered ? 'Speech Detected!' : 'Listening…'}
            </span>
          </div>

          <div className="mic-meter-bar-track" aria-hidden="true">
            <div
              className={`mic-meter-bar-fill ${
                isSpeechTriggered ? 'triggered' : ''
              }`}
              style={{ width: `${meterPercent}%` }}
            />
            {/* Threshold Marker Indicator */}
            <div
              className="mic-meter-threshold-line"
              style={{ left: `${thresholdPercent}%` }}
              title={`Speech threshold: ${threshold.toFixed(3)}`}
            />
          </div>

          <div className="mic-meter-footer">
            <span className="level-text">
              Current RMS: {currentLevel.toFixed(4)}
            </span>
            <span className="threshold-text">
              Cutoff Threshold: {threshold.toFixed(4)}
            </span>
          </div>
        </div>

        {/* ── 3-Second Auto-Calibration ── */}
        <div className="mic-autocalib-box">
          <div className="autocalib-info">
            <Zap size={18} className="autocalib-icon" aria-hidden="true" />
            <div>
              <strong>Calibrate Classroom Noise Floor</strong>
              <p>
                Stay quiet for 3 seconds so the app can measure room fans or AC
                noise.
              </p>
            </div>
          </div>

          {isCalibrating ? (
            <div className="autocalib-progress-wrapper">
              <div
                className="autocalib-progress-bar"
                style={{ width: `${calibProgress}%` }}
              />
              <span className="autocalib-progress-text">
                Measuring ambient noise… {calibProgress}%
              </span>
            </div>
          ) : (
            <button
              type="button"
              className="button primary small"
              id="btn-auto-calibrate-noise"
              onClick={runAutoCalibration}
            >
              Start 3-Sec Calibration
            </button>
          )}

          {calibSuccess && (
            <div className="autocalib-success-banner" role="status">
              <CheckCircle2 size={16} aria-hidden="true" />
              <span>Calibrated! Threshold adjusted to {threshold.toFixed(4)}.</span>
            </div>
          )}
        </div>

        {/* ── Sensitivity Presets ── */}
        <div className="mic-presets-section">
          <label className="section-label">Sensitivity Presets:</label>
          <div className="mic-presets-grid">
            {PRESETS.map((p) => {
              const isSelected = Math.abs(threshold - p.value) < 0.004
              return (
                <button
                  key={p.label}
                  type="button"
                  className={`preset-card ${isSelected ? 'selected' : ''}`}
                  onClick={() => handleSelectPreset(p.value)}
                >
                  <span className="preset-name">{p.label}</span>
                  <span className="preset-sublabel">{p.sublabel}</span>
                </button>
              )
            })}
          </div>
        </div>

        {/* ── Manual Slider ── */}
        <div className="mic-slider-section">
          <div className="slider-header">
            <span className="section-label">Fine Sensitivity Tuning:</span>
            <span className="slider-val">{threshold.toFixed(4)}</span>
          </div>
          <input
            type="range"
            min="0.008"
            max="0.065"
            step="0.002"
            value={threshold}
            onChange={handleSliderChange}
            className="mic-slider"
            aria-label="Microphone sensitivity threshold"
          />
          <div className="slider-markers">
            <span>High Sensitivity (Quiet)</span>
            <span>Balanced</span>
            <span>Low Sensitivity (Loud)</span>
          </div>
        </div>

        {/* ── Echo Gate Status Protection Info ── */}
        <div className="echo-gate-info-card">
          <ShieldCheck size={20} className="echo-shield-icon" aria-hidden="true" />
          <div className="echo-text">
            <strong>Acoustic Echo Gate Active</strong>
            <p>
              Microphone recording is automatically suspended while educational
              speech synthesis plays, preventing self-transcription feedback loops.
            </p>
          </div>
        </div>

        {/* ── Modal Footer ── */}
        <div className="modal-footer">
          <button
            type="button"
            className="button secondary small"
            onClick={handleResetDefault}
          >
            Reset Default
          </button>
          <button
            type="button"
            className="button primary small"
            onClick={onClose}
          >
            Save & Close
          </button>
        </div>
      </div>
    </div>
  )
}
