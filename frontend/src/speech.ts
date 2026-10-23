import { voiceDiagnostic } from './voiceDiagnostics'

let cachedVoice: SpeechSynthesisVoice | null | undefined = undefined // undefined = not yet resolved

export const speechSupported = () =>
  typeof window !== 'undefined' &&
  'speechSynthesis' in window &&
  'SpeechSynthesisUtterance' in window

// ─── Speech rate ──────────────────────────────────────────────────────────────

const SPEECH_RATE_KEY = 'v2l-speech-rate'
const SPEECH_RATE_DEFAULT = 0.95
const SPEECH_RATE_MIN = 0.8
const SPEECH_RATE_MAX = 1.15

export function getStoredSpeechRate(): number {
  if (typeof window === 'undefined') return SPEECH_RATE_DEFAULT
  const val = parseFloat(localStorage.getItem(SPEECH_RATE_KEY) || '')
  if (isNaN(val)) return SPEECH_RATE_DEFAULT
  return Math.min(SPEECH_RATE_MAX, Math.max(SPEECH_RATE_MIN, val))
}

export function setStoredSpeechRate(rate: number) {
  const clamped = Math.min(SPEECH_RATE_MAX, Math.max(SPEECH_RATE_MIN, rate))
  if (typeof window !== 'undefined') {
    localStorage.setItem(SPEECH_RATE_KEY, clamped.toFixed(2))
  }
  return clamped
}

// ─── English voice selection ──────────────────────────────────────────────────

/** Preferred locale tags in priority order (Indian English first). */
const PREFERRED_LOCALES = ['en-IN', 'en-GB', 'en-US', 'en-AU', 'en']

function scoreVoice(voice: SpeechSynthesisVoice): number {
  const lang = voice.lang.toLowerCase()
  const name = voice.name.toLowerCase()
  const idx = PREFERRED_LOCALES.findIndex((loc) => lang.startsWith(loc.toLowerCase()))
  if (idx === -1) return -1 // non-English voice — skip
  let score = (PREFERRED_LOCALES.length - idx) * 10
  // Prefer non-default remote (Google/Natural) voices for clarity
  if (name.includes('google')) score += 5
  if (name.includes('natural') || name.includes('enhanced')) score += 3
  if (voice.localService) score -= 2 // slight penalty for OS voices (can be robotic)
  return score
}

function selectBestVoice(): SpeechSynthesisVoice | null {
  if (!speechSupported()) return null
  const voices = window.speechSynthesis.getVoices()
  if (!voices.length) return null
  let best: SpeechSynthesisVoice | null = null
  let bestScore = -Infinity
  for (const v of voices) {
    const s = scoreVoice(v)
    if (s > bestScore) {
      bestScore = s
      best = v
    }
  }
  return bestScore >= 0 ? best : null
}

/** Returns a resolved voice, triggering async load if voices are not yet available. */
function getVoice(): SpeechSynthesisVoice | null {
  if (cachedVoice !== undefined) return cachedVoice
  const selected = selectBestVoice()
  if (selected !== null || window.speechSynthesis.getVoices().length > 0) {
    cachedVoice = selected
    return cachedVoice
  }
  // Voices not loaded yet — hook into voiceschanged and return null for now
  cachedVoice = null
  window.speechSynthesis.addEventListener(
    'voiceschanged',
    () => {
      cachedVoice = selectBestVoice()
    },
    { once: true }
  )
  return null
}

// ─── Educational text normalisation ──────────────────────────────────────────

// Fraction word map for simple fractions
const FRACTION_WORDS: Record<string, string> = {
  '1/2': 'one half',
  '1/3': 'one third',
  '2/3': 'two thirds',
  '1/4': 'one quarter',
  '3/4': 'three quarters',
  '1/5': 'one fifth',
  '2/5': 'two fifths',
  '3/5': 'three fifths',
  '4/5': 'four fifths',
  '1/8': 'one eighth',
  '3/8': 'three eighths',
  '5/8': 'five eighths',
  '7/8': 'seven eighths',
}

// Common unit abbreviations
const UNIT_MAP: Array<[RegExp, string]> = [
  [/\b(\d+)\s*km\/h\b/gi, '$1 kilometers per hour'],
  [/\b(\d+)\s*m\/s\b/gi, '$1 meters per second'],
  [/\b(\d+)\s*cm\b/gi, '$1 centimeters'],
  [/\b(\d+)\s*km\b/gi, '$1 kilometers'],
  [/\b(\d+)\s*mm\b/gi, '$1 millimeters'],
  [/\b(\d+)\s*kg\b/gi, '$1 kilograms'],
  [/\b(\d+)\s*g\b(?![\w])/gi, '$1 grams'],
  [/\b(\d+)\s*mg\b/gi, '$1 milligrams'],
  [/\b(\d+)\s*l\b/gi, '$1 liters'],
  [/\b(\d+)\s*ml\b/gi, '$1 milliliters'],
  [/\b(\d+)\s*°C\b/gi, '$1 degrees Celsius'],
  [/\b(\d+)\s*°F\b/gi, '$1 degrees Fahrenheit'],
  [/\b(\d+)\s*m\b(?![\w])/gi, '$1 meters'],
  [/\b(\d+)%\b/gi, '$1 percent'],
]

// Common chemical/scientific symbols → spoken form
const CHEMICAL_MAP: Array<[RegExp, string]> = [
  [/\bH2O\b/gi, 'H 2 O'],
  [/\bCO2\b/gi, 'C O 2'],
  [/\bO2\b/gi, 'O 2'],
  [/\bN2\b/gi, 'N 2'],
  [/\bCO\b(?=[\s,.])/g, 'C O'],
  [/\bNaCl\b/gi, 'sodium chloride'],
  [/\bHCl\b/gi, 'H C l'],
  [/\bH2SO4\b/gi, 'H 2 S O 4'],
  [/\bNaOH\b/gi, 'N A O H'],
]

/**
 * Normalises educational text for clear English pronunciation:
 *  - Simple fractions (1/2 → "one half")
 *  - Measurement units (10 cm → "10 centimeters")
 *  - Chemical formulas (H2O → "H 2 O")
 * Complex fraction expressions (e.g. "3/7") are left intact and spoken digit-by-digit.
 */
export function normalizeEducationalText(text: string): string {
  let out = text

  // Simple named fractions
  for (const [frac, word] of Object.entries(FRACTION_WORDS)) {
    out = out.split(frac).join(word)
  }

  // Unit abbreviations
  for (const [pattern, replacement] of UNIT_MAP) {
    out = out.replace(pattern, replacement)
  }

  // Chemical symbols
  for (const [pattern, replacement] of CHEMICAL_MAP) {
    out = out.replace(pattern, replacement)
  }

  return out
}

// ─── Core TTS API ─────────────────────────────────────────────────────────────

let activeUtterance: SpeechSynthesisUtterance | null = null
let isActivelySpeaking = false
let currentUtteranceId = 0

function notifySpeakingChange(speaking: boolean) {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('tts-speaking-change', { detail: { speaking } }))
  }
}

/**
 * Stop any current speech synthesis cleanly and idempotently.
 * Only emits speaking: false if speech was actively speaking.
 */
export function stopSpeaking() {
  if (!speechSupported()) return
  currentUtteranceId += 1
  const wasSpeaking = isActivelySpeaking
  activeUtterance = null
  isActivelySpeaking = false

  try {
    window.speechSynthesis.cancel()
  } catch (err) {
    console.warn('[speech] speechSynthesis.cancel error:', err)
  }

  if (wasSpeaking) {
    notifySpeakingChange(false)
  }
}

/**
 * Speak `text` using the browser's SpeechSynthesis API.
 * Text is normalised for educational pronunciation before speaking.
 * Emits `tts-speaking-change` events for the acoustic echo gate.
 *
 * @param text - The educational text to speak.
 * @param onEnd - Optional callback invoked when speaking finishes or errors.
 * @returns `true` if speech was initiated, `false` if unavailable.
 */
export function speakText(text: string, onEnd?: () => void): boolean {
  if (!speechSupported() || !text.trim()) return false
  stopSpeaking()

  currentUtteranceId += 1
  const utteranceId = currentUtteranceId

  const normalised = normalizeEducationalText(text)
  const utterance = new SpeechSynthesisUtterance(normalised)
  const startedAt = voiceDiagnostic('tts-start')
  activeUtterance = utterance

  // Apply voice preference
  const voice = getVoice()
  if (voice) utterance.voice = voice

  // Apply configurable rate
  utterance.rate = getStoredSpeechRate()
  utterance.pitch = 1.0

  let finished = false
  const finish = () => {
    if (finished || utteranceId !== currentUtteranceId) return
    finished = true
    if (activeUtterance === utterance) {
      activeUtterance = null
    }
    const wasSpeaking = isActivelySpeaking
    isActivelySpeaking = false
    if (wasSpeaking) {
      notifySpeakingChange(false)
    }
    voiceDiagnostic('tts-end', startedAt)
    onEnd?.()
  }

  utterance.onstart = () => {
    if (utteranceId !== currentUtteranceId || activeUtterance !== utterance) return
    isActivelySpeaking = true
    notifySpeakingChange(true)
  }

  utterance.onend = finish
  utterance.onerror = finish

  try {
    window.speechSynthesis.speak(utterance)
    return true
  } catch (err) {
    console.error('[speech] speechSynthesis.speak error:', err)
    finish()
    return false
  }
}

/**
 * Check if the application is currently speaking an active educational utterance.
 * Guarded against browser ghost flags where window.speechSynthesis.speaking remains stuck.
 */
export function isSpeaking(): boolean {
  if (!speechSupported()) return false
  return isActivelySpeaking || activeUtterance !== null
}
