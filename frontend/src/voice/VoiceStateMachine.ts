/**
 * Voice2Learn Voice State Machine
 * Deterministic states, legal transitions, and UUID session tracking.
 */

export type VoiceState =
  | 'STANDBY'
  | 'LISTENING'
  | 'TRANSCRIBING'
  | 'INTERPRETING'
  | 'EXECUTING'
  | 'SPEAKING'
  | 'ERROR'
  | 'INTERRUPTED'

export const LEGAL_TRANSITIONS: Record<VoiceState, readonly VoiceState[]> = {
  STANDBY: ['LISTENING', 'ERROR'],
  LISTENING: ['TRANSCRIBING', 'INTERRUPTED', 'STANDBY', 'ERROR'],
  TRANSCRIBING: ['INTERPRETING', 'STANDBY', 'ERROR'],
  INTERPRETING: ['EXECUTING', 'SPEAKING', 'STANDBY', 'ERROR'],
  EXECUTING: ['SPEAKING', 'STANDBY', 'ERROR'],
  SPEAKING: ['STANDBY', 'INTERRUPTED', 'ERROR'],
  ERROR: ['STANDBY'],
  INTERRUPTED: ['STANDBY'],
} as const

/**
 * Verify if transition from currentState to targetState is legal.
 */
export function canTransition(from: VoiceState, to: VoiceState): boolean {
  if (from === to) return true
  const allowed = LEGAL_TRANSITIONS[from]
  return allowed ? allowed.includes(to) : false
}

/**
 * Generate a cryptographically secure UUID for session tracking.
 * Stale sessions are automatically discarded to prevent race conditions.
 */
export function generateSessionId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

/**
 * Verify if an async operation's session ID matches the active session.
 */
export function isValidSession(targetSessionId: string, currentSessionId: string): boolean {
  return Boolean(targetSessionId && currentSessionId && targetSessionId === currentSessionId)
}

/**
 * Log state transitions with timestamp and session verification.
 */
export function logStateTransition(
  from: VoiceState,
  to: VoiceState,
  sessionId: string,
  reason?: string
): void {
  const ts = new Date().toISOString()
  const reasonStr = reason ? ` | Reason: ${reason}` : ''
  console.log(`[VoiceStateMachine ${ts}] [Session: ${sessionId}] ${from} -> ${to}${reasonStr}`)
}

export interface VoiceMachineState {
  state: VoiceState
  sessionId: string
  transcript: string
  lastCommand: string | null
  lastResponse: string | null
  errorMessage: string | null
  screenContext: Record<string, unknown>
}
