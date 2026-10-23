import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { BookOpen, Mic, MicOff, Shield, SlidersHorizontal } from 'lucide-react'
import { useVoice } from '../../useVoice'
import { speakText, stopSpeaking } from '../../speech'
import { voiceDiagnostic } from '../../voiceDiagnostics'
import { getActivePosition, runAgent } from '../../api'
import { MicSensitivityModal } from './MicSensitivityModal'
import type { VoiceContext } from '../../types'

const HELP_GUIDANCE =
  'Supported English voice commands: open dashboard, open lesson, open quiz or start quiz, show my progress, go back, read lesson or question, repeat that, select option A, B, C, or D, submit answer, next question, stop speaking, stop listening, cancel, and help. You can also ask any question about your lessons.'

export function VoiceStatusBar() {
  const navigate = useNavigate()
  const location = useLocation()
  const [contextDetails, setContextDetails] = useState<VoiceContext>({})
  const [message, setMessage] = useState('Voice control ready.')
  const [calibrationOpen, setCalibrationOpen] = useState(false)

  const context = useMemo<VoiceContext>(
    () => ({
      ...contextDetails,
      screen: location.pathname,
      active_quiz: location.pathname === '/quiz',
    }),
    [contextDetails, location.pathname]
  )

  const voice = useVoice(context)
  const { reset: resetVoice, stop: stopVoice } = voice

  const dispatch = (action: string) =>
    window.dispatchEvent(new CustomEvent('voice-command', { detail: { action } }))

  const command = voice.result?.interpretation.command
  const transcript = voice.result?.text
  const pipelineStartedAt = voice.result?.startedAt
  const response = voice.result?.interpretation.response
  const clarification = voice.result?.interpretation.clarification

  useEffect(() => {
    voiceDiagnostic('screen-transition')
    stopSpeaking()
    return () => stopSpeaking()
  }, [location.pathname])

  useEffect(() => {
    const handler = (event: Event) =>
      setContextDetails((event as CustomEvent<VoiceContext>).detail)
    window.addEventListener('voice-context', handler)
    return () => window.removeEventListener('voice-context', handler)
  }, [])

  useEffect(() => {
    if (voice.state !== 'done') return

    if (!command) {
      if (transcript && voice.state === 'done') {
        // 1. If it's a curriculum educational question with a grounded answer, speak it
        if (voice.result?.interpretation.intent === 'question' && response) {
          setMessage(response)
          speakText(response)
          return
        }

        // 2. Delegate natural-language requests to the AI Browser Agent
        void (async () => {
          try {
            setMessage('Consulting AI browser agent…')
            let learnerId = 'demo-learner'
            try {
              const raw = localStorage.getItem('v2l-learner')
              if (raw) {
                const parsed = JSON.parse(raw)
                if (parsed?.id) learnerId = parsed.id
              }
            } catch {
              // fallback
            }

            const agentResp = await runAgent(transcript, {
              learner_id: learnerId,
              current_url: location.pathname,
              page_title: document.title,
            })

            const agentMessage = agentResp.final_message || 'Task processed.'

            // Route validation against allowed routes (supports query parameters e.g. /quiz?subject=english)
            const allowedStaticRoutes = ['/dashboard', '/quiz', '/progress', '/login', '/register']
            const basePath = agentResp.target_url ? agentResp.target_url.split('?')[0].trim() : ''
            const isValidRoute =
              agentResp.target_url &&
              (allowedStaticRoutes.includes(basePath) ||
                /^\/concept\/[a-zA-Z0-9_-]+$/.test(basePath))

            console.log(`🎙️ [Student Speech]: "${transcript}"`)
            console.log(`🤖 [AI Browser Agent]: Target URL: ${agentResp.target_url || 'None'} | Response: "${agentMessage}"`)

            if (agentResp.target_url && isValidRoute && agentResp.status === 'completed') {
              navigate(agentResp.target_url)
              setMessage(agentMessage)
              speakText(agentMessage)
            } else if (agentResp.status === 'needs_clarification' || !agentResp.target_url) {
              setMessage(agentMessage)
              speakText(agentMessage)
            } else {
              const fallbackMsg =
                response ||
                clarification ||
                agentMessage ||
                "I'm not sure what you want to do. Could you say that another way?"
              setMessage(fallbackMsg)
              speakText(fallbackMsg)
            }
          } catch (agentErr) {
            console.error('Agent runtime call failed:', agentErr)
            const fallbackMsg =
              response ||
              clarification ||
              "I'm not sure what you want to do. Could you say that another way?"
            setMessage(fallbackMsg)
            speakText(fallbackMsg)
          }
        })()
      }
      return
    }

    const handleOpenLesson = async () => {
      try {
        let learnerId = 'demo-learner'
        const raw = localStorage.getItem('v2l-learner')
        if (raw) {
          const parsed = JSON.parse(raw)
          if (parsed?.id) learnerId = parsed.id
        }

        const lowerTranscript = transcript?.toLowerCase() || ''
        const targetSubject = lowerTranscript.includes('science')
          ? 'science'
          : lowerTranscript.includes('math')
          ? 'mathematics'
          : lowerTranscript.includes('english')
          ? 'english'
          : lowerTranscript.includes('social')
          ? 'social_science'
          : undefined

        const posResp = await getActivePosition(learnerId, targetSubject)
        if (posResp?.concept_id) {
          navigate(`/concept/${posResp.concept_id}`)
          return
        }
      } catch {
        // fallback
      }

      const lower = transcript?.toLowerCase() || ''
      if (lower.includes('math')) {
        navigate('/concept/math-ch01-c01')
      } else if (lower.includes('english')) {
        navigate('/concept/eng-ch01-c01')
      } else if (lower.includes('social')) {
        navigate('/concept/soc-ch01-c01')
      } else {
        navigate('/concept/sci-ch01-c01')
      }
    }

    const handleOpenQuiz = () => {
      const lower = transcript?.toLowerCase() || ''
      const targetSubject = lower.includes('social')
        ? 'social_science'
        : lower.includes('math')
        ? 'mathematics'
        : lower.includes('english')
        ? 'english'
        : lower.includes('science')
        ? 'science'
        : undefined

      if (targetSubject) {
        navigate(`/quiz?subject=${targetSubject}`)
      } else {
        navigate('/quiz')
      }
    }

    const actions: Record<string, () => void> = {
      OPEN_DASHBOARD: () => navigate('/dashboard'),
      OPEN_LESSON: () => { void handleOpenLesson() },
      START_LESSON: () => { void handleOpenLesson() },
      SELECT_SUBJECT: () => { void handleOpenLesson() },
      OPEN_QUIZ: handleOpenQuiz,
      SHOW_PROGRESS: () => navigate('/progress'),
      GO_BACK: () => navigate(-1),
      STOP_SPEAKING: stopSpeaking,
      STOP: stopSpeaking,
      STOP_LISTENING: stopVoice,
      CANCEL: () => {
        stopSpeaking()
        resetVoice()
      },
      HELP: () => {
        setMessage(HELP_GUIDANCE)
        speakText(HELP_GUIDANCE)
      },
      REPEAT: () => dispatch('REPEAT'),
      READ_LESSON: () => dispatch('READ_LESSON'),
      NEXT_SECTION: () => dispatch('NEXT_SECTION'),
      READ_QUESTION: () => dispatch('READ_QUESTION'),
      SELECT_OPTION_A: () => dispatch('SELECT_OPTION_A'),
      SELECT_OPTION_B: () => dispatch('SELECT_OPTION_B'),
      SELECT_OPTION_C: () => dispatch('SELECT_OPTION_C'),
      SELECT_OPTION_D: () => dispatch('SELECT_OPTION_D'),
      SUBMIT_ANSWER: () => dispatch('SUBMIT_ANSWER'),
      NEXT_QUESTION: () => dispatch('NEXT_QUESTION'),
      CONFIRM: () => dispatch('SUBMIT_ANSWER'),
      HINT: () => dispatch('HINT'),
      GIVE_HINT: () => dispatch('HINT'),
      NEXT_CONCEPT: () => dispatch('NEXT_CONCEPT'),
      PREV_CONCEPT: () => dispatch('PREV_CONCEPT'),
    }

    console.log(`🎙️ [Student Speech]: "${transcript}"`)
    console.log(`👉 [Website Action]: Executed ${command}`)
    actions[command]?.()
    voiceDiagnostic(`frontend-dispatch:${command}`, pipelineStartedAt)
    if (command !== 'HELP') {
      setMessage(`Command completed: ${command.replace(/_/g, ' ').toLowerCase()}.`)
    }
  }, [
    clarification,
    command,
    navigate,
    pipelineStartedAt,
    resetVoice,
    response,
    stopVoice,
    transcript,
    voice.state,
    location.pathname,
  ])

  const statusText = voice.isEchoGated
    ? 'Echo gate active · Speaker playing…'
    : voice.state === 'recording'
    ? 'Listening… speak clearly'
    : voice.state === 'processing'
    ? 'Processing speech…'
    : voice.state === 'error'
    ? `Retrying: ${voice.error}`
    : voice.enabled
    ? 'Voice control active'
    : message

  return (
    <>
      <div
        className={`global-voice ${voice.enabled ? 'active' : ''} ${
          voice.isEchoGated ? 'echo-gated' : ''
        }`}
        role="region"
        aria-label="Voice Control Bar"
      >
        <span className="voice-indicator" aria-hidden="true" />
        <span aria-live="polite" className="voice-status-text">
          {statusText}
        </span>
        {voice.isEchoGated && (
          <span className="echo-gate-badge" title="Microphone muted during computer speaker output">
            <Shield size={13} aria-hidden="true" />
            <span>Echo Guard</span>
          </span>
        )}
        {voice.result?.interpretation.source && (
          <span
            className="curriculum-source-badge"
            title={`Source: Class 6 ${voice.result.interpretation.source.subject_name} — ${voice.result.interpretation.source.chapter_title}`}
          >
            <BookOpen size={13} aria-hidden="true" />
            <span>{voice.result.interpretation.source.chapter_title}</span>
          </span>
        )}
        <div className="voice-actions-group">
          <button
            type="button"
            id="btn-voice-calibrate"
            aria-label="Calibrate microphone sensitivity"
            title="Calibrate microphone and noise floor"
            onClick={() => setCalibrationOpen(true)}
            className="voice-settings-btn"
          >
            <SlidersHorizontal size={16} aria-hidden="true" />
          </button>
          <button
            type="button"
            id="toggle-voice-btn"
            aria-label={voice.enabled ? 'Stop voice control' : 'Start voice control'}
            aria-pressed={voice.enabled}
            onClick={voice.enabled ? voice.stop : voice.start}
            className={`voice-toggle-btn ${voice.enabled ? 'recording' : ''}`}
          >
            {voice.enabled ? <MicOff size={18} /> : <Mic size={18} />}
            <span>{voice.enabled ? 'Stop Voice' : 'Voice Control'}</span>
          </button>
        </div>
      </div>

      <MicSensitivityModal
        isOpen={calibrationOpen}
        onClose={() => setCalibrationOpen(false)}
      />
    </>
  )
}
