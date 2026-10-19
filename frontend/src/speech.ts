import { voiceDiagnostic } from './voiceDiagnostics'

let activeUtterance: SpeechSynthesisUtterance | null = null
export const speechSupported = () => typeof window !== 'undefined' && 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window

export function stopSpeaking() {
  if (!speechSupported()) return
  window.speechSynthesis.cancel()
  activeUtterance = null
}

export function speakText(text: string, onEnd?: () => void): boolean {
  if (!speechSupported() || !text.trim()) return false
  stopSpeaking()
  const utterance = new SpeechSynthesisUtterance(text)
  const startedAt = voiceDiagnostic('tts-start')
  activeUtterance = utterance
  const finish = () => {
    if (activeUtterance === utterance) activeUtterance = null
    voiceDiagnostic('tts-end', startedAt)
    onEnd?.()
  }

  utterance.onend = finish
  utterance.onerror = finish
  window.speechSynthesis.speak(utterance)
  return true
}

export function isSpeaking() {
  return speechSupported() && window.speechSynthesis.speaking
}
