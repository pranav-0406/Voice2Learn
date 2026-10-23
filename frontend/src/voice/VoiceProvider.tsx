import React, { createContext, useCallback, useEffect, useRef, useState } from 'react'
import {
  canTransition,
  generateSessionId,
  isValidSession,
  logStateTransition,
  type VoiceMachineState,
  type VoiceState,
} from './VoiceStateMachine'
import { AudioCapture } from './AudioCapture'

export interface VoiceContextValue extends VoiceMachineState {
  startListening: (reason?: string) => string
  stopListening: (reason?: string) => void
  cancelSession: (reason?: string) => void
  setScreenContext: (context: Record<string, unknown>) => void
  transitionState: (
    nextState: VoiceState,
    sessionId: string,
    meta?: {
      reason?: string
      transcript?: string
      command?: string | null
      response?: string | null
      error?: string | null
    }
  ) => boolean
  isSessionActive: (sessionId: string) => boolean
}

export const VoiceContext = createContext<VoiceContextValue | null>(null)

interface VoiceProviderProps {
  children: React.ReactNode
}

export function VoiceProvider({ children }: VoiceProviderProps) {
  const [machineState, setMachineState] = useState<VoiceMachineState>({
    state: 'STANDBY',
    sessionId: '',
    transcript: '',
    lastCommand: null,
    lastResponse: null,
    errorMessage: null,
    screenContext: {},
  })

  // Ref tracking current active session to protect async operations from race conditions
  const currentSessionIdRef = useRef<string>('')
  const stateRef = useRef<VoiceState>('STANDBY')
  stateRef.current = machineState.state

  const autoRecoverTimerRef = useRef<number | null>(null)
  const audioCaptureRef = useRef<AudioCapture | null>(null)

  if (!audioCaptureRef.current) {
    audioCaptureRef.current = new AudioCapture()
  }

  const clearAutoRecoverTimer = useCallback(() => {
    if (autoRecoverTimerRef.current !== null) {
      window.clearTimeout(autoRecoverTimerRef.current)
      autoRecoverTimerRef.current = null
    }
  }, [])

  const isSessionActive = useCallback((targetSessionId: string): boolean => {
    return isValidSession(targetSessionId, currentSessionIdRef.current)
  }, [])

  const transitionState = useCallback(
    (
      nextState: VoiceState,
      targetSessionId: string,
      meta?: {
        reason?: string
        transcript?: string
        command?: string | null
        response?: string | null
        error?: string | null
      }
    ): boolean => {
      const currentState = stateRef.current

      // Stale session check: async callbacks with old session IDs are discarded
      if (!isValidSession(targetSessionId, currentSessionIdRef.current)) {
        console.warn(
          `[VoiceStateMachine] Discarded stale operation for session ${targetSessionId} (active: ${currentSessionIdRef.current})`
        )
        return false
      }

      // Legal transition check
      if (!canTransition(currentState, nextState)) {
        console.warn(
          `[VoiceStateMachine] Illegal transition attempted: ${currentState} -> ${nextState} (Session: ${targetSessionId})`
        )
        return false
      }

      logStateTransition(currentState, nextState, targetSessionId, meta?.reason)

      clearAutoRecoverTimer()

      setMachineState((prev) => ({
        ...prev,
        state: nextState,
        transcript: meta?.transcript !== undefined ? meta.transcript : prev.transcript,
        lastCommand: meta?.command !== undefined ? meta.command : prev.lastCommand,
        lastResponse: meta?.response !== undefined ? meta.response : prev.lastResponse,
        errorMessage: meta?.error !== undefined ? meta.error : null,
      }))

      // Handle auto-recovery timers for terminal or transient states
      if (nextState === 'ERROR') {
        autoRecoverTimerRef.current = window.setTimeout(() => {
          if (stateRef.current === 'ERROR' && currentSessionIdRef.current === targetSessionId) {
            logStateTransition('ERROR', 'STANDBY', targetSessionId, 'Auto-recovered after error timeout')
            setMachineState((prev) => ({
              ...prev,
              state: 'STANDBY',
              errorMessage: null,
            }))
          }
        }, 3000)
      } else if (nextState === 'INTERRUPTED') {
        autoRecoverTimerRef.current = window.setTimeout(() => {
          if (stateRef.current === 'INTERRUPTED' && currentSessionIdRef.current === targetSessionId) {
            logStateTransition('INTERRUPTED', 'STANDBY', targetSessionId, 'Cleaned up interrupted state')
            setMachineState((prev) => ({
              ...prev,
              state: 'STANDBY',
            }))
          }
        }, 300)
      }

      return true
    },
    [clearAutoRecoverTimer]
  )

  const stopListening = useCallback(
    (reason = 'Stop listening requested') => {
      audioCaptureRef.current?.stop()
      const activeSession = currentSessionIdRef.current
      if (stateRef.current === 'LISTENING') {
        transitionState('STANDBY', activeSession, { reason })
      }
    },
    [transitionState]
  )

  const cancelSession = useCallback(
    (reason = 'Session cancelled') => {
      audioCaptureRef.current?.abort()
      const activeSession = currentSessionIdRef.current
      if (stateRef.current !== 'STANDBY') {
        if (canTransition(stateRef.current, 'INTERRUPTED')) {
          transitionState('INTERRUPTED', activeSession, { reason })
        } else {
          // Direct fallback to STANDBY
          logStateTransition(stateRef.current, 'STANDBY', activeSession, reason)
          clearAutoRecoverTimer()
          setMachineState((prev) => ({
            ...prev,
            state: 'STANDBY',
          }))
        }
      }
    },
    [transitionState, clearAutoRecoverTimer]
  )

  const startListening = useCallback(
    (reason = 'User activated voice input'): string => {
      const newSessionId = generateSessionId()
      currentSessionIdRef.current = newSessionId
      clearAutoRecoverTimer()

      const currentState = stateRef.current
      if (!canTransition(currentState, 'LISTENING')) {
        console.warn(`[VoiceStateMachine] Cannot start listening from state: ${currentState}`)
        // Force reset to STANDBY first if somehow stuck
        logStateTransition(currentState, 'STANDBY', newSessionId, 'Resetting stuck state before activation')
      }

      logStateTransition(currentState, 'LISTENING', newSessionId, reason)

      setMachineState((prev) => ({
        ...prev,
        state: 'LISTENING',
        sessionId: newSessionId,
        transcript: '',
        errorMessage: null,
      }))

      // Initiate single-utterance audio capture
      void audioCaptureRef.current?.start(newSessionId, {
        onSpeechStart: (session) => {
          console.log(`[VoiceProvider] Speech detected for session ${session}`)
        },
        onSpeechEnd: (session) => {
          console.log(`[VoiceProvider] Trailing silence reached for session ${session}`)
        },
        onAudioData: (audioBlob, session) => {
          if (!isValidSession(session, currentSessionIdRef.current)) return
          console.log(`[VoiceProvider] Captured audio blob (${audioBlob.size} bytes) for session ${session}`)
          if (canTransition(stateRef.current, 'TRANSCRIBING')) {
            transitionState('TRANSCRIBING', session, { reason: 'Audio capture complete' })
            // Handover to STANDBY until Module 5 transcription pipeline is wired
            transitionState('STANDBY', session, { reason: 'Awaiting Module 5 STT integration' })
          }
        },
        onError: (err, session) => {
          if (!isValidSession(session, currentSessionIdRef.current)) return
          console.error(`[VoiceProvider] Audio capture error for session ${session}:`, err)
          transitionState('ERROR', session, {
            error: err.message || 'Microphone error',
            reason: 'Audio capture failure',
          })
        },
      })

      return newSessionId
    },
    [clearAutoRecoverTimer, transitionState]
  )

  const setScreenContext = useCallback((context: Record<string, unknown>) => {
    setMachineState((prev) => ({
      ...prev,
      screenContext: context,
    }))
  }, [])

  // Listen for global voice-stop event (e.g. on logout) and unmount cleanup
  useEffect(() => {
    const handleVoiceStop = () => {
      cancelSession('Global voice-stop event received')
    }
    window.addEventListener('voice-stop', handleVoiceStop)
    return () => {
      window.removeEventListener('voice-stop', handleVoiceStop)
      clearAutoRecoverTimer()
      audioCaptureRef.current?.abort()
    }
  }, [cancelSession, clearAutoRecoverTimer])

  const contextValue: VoiceContextValue = {
    ...machineState,
    startListening,
    stopListening,
    cancelSession,
    setScreenContext,
    transitionState,
    isSessionActive,
  }

  return <VoiceContext.Provider value={contextValue}>{children}</VoiceContext.Provider>
}
