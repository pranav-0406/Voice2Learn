import { useContext, useMemo } from 'react'
import { VoiceContext, type VoiceContextValue } from './VoiceProvider'

export interface VoiceController extends VoiceContextValue {
  isStandby: boolean
  isListening: boolean
  isTranscribing: boolean
  isInterpreting: boolean
  isExecuting: boolean
  isSpeaking: boolean
  isError: boolean
  isInterrupted: boolean
  isBusy: boolean
}

/**
 * Primary hook to interact with the Voice2Learn centralized voice controller.
 */
export function useVoiceController(): VoiceController {
  const context = useContext(VoiceContext)

  if (!context) {
    throw new Error('useVoiceController must be used within a <VoiceProvider>')
  }

  const { state } = context

  const derivedFlags = useMemo(() => {
    return {
      isStandby: state === 'STANDBY',
      isListening: state === 'LISTENING',
      isTranscribing: state === 'TRANSCRIBING',
      isInterpreting: state === 'INTERPRETING',
      isExecuting: state === 'EXECUTING',
      isSpeaking: state === 'SPEAKING',
      isError: state === 'ERROR',
      isInterrupted: state === 'INTERRUPTED',
      isBusy: state === 'TRANSCRIBING' || state === 'INTERPRETING' || state === 'EXECUTING',
    }
  }, [state])

  return {
    ...context,
    ...derivedFlags,
  }
}
