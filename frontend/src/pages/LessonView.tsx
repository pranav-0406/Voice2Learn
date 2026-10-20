import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  ChevronRight,
  Mic,
  Sparkles,
  Star,
  Volume2,
} from 'lucide-react'
import {
  Button,
  Card,
  Page,
  PageError,
} from '../components/ui'
import { getLesson } from '../api'
import { speakText, speechSupported } from '../speech'
import type { Lesson } from '../types'

export function LessonView() {
  const { id = 'science-measurements' } = useParams<{ id: string }>()
  const [lesson, setLesson] = useState<Lesson | null>(null)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    if (id && (id.startsWith('sci-') || id.startsWith('eng-') || id.startsWith('math-') || id.startsWith('soc-'))) {
      navigate(`/concept/${encodeURIComponent(id)}`, { replace: true })
    }
  }, [id, navigate])

  useEffect(() => {
    let alive = true
    getLesson(id)
      .then(item => {
        if (alive) setLesson(item)
      })
      .catch(cause => {
        if (alive) setError(cause instanceof Error ? cause.message : 'Lesson not found.')
      })
    return () => {
      alive = false
    }
  }, [id])

  useEffect(() => {
    if (!lesson) return
    const narration = [
      lesson.content.summary,
      ...(lesson.content.key_points || []),
    ]
      .filter(Boolean)
      .join('. ')

    window.dispatchEvent(
      new CustomEvent('voice-context', {
        detail: { lesson_topic: lesson.topic },
      })
    )

    const handler = (event: Event) => {
      const action = (event as CustomEvent<{ action: string }>).detail.action
      if (action === 'READ_LESSON' || action === 'REPEAT') {
        speakText(narration)
      }
    }

    window.addEventListener('voice-command', handler)
    return () => window.removeEventListener('voice-command', handler)
  }, [lesson])

  if (error) return <PageError message={error} />
  if (!lesson) {
    return (
      <Page id="lesson-loading">
        <div className="skeleton-stack" aria-busy="true">
          <div className="skeleton title" />
          <div className="skeleton block" />
          <div className="skeleton block" />
        </div>
      </Page>
    )
  }

  const { content } = lesson
  const narration = [
    content.summary,
    ...(content.key_points || []),
  ]
    .filter(Boolean)
    .join('. ')

  return (
    <Page id="lesson-view">
      <header className="lesson-header">
        <p className="eyebrow">
          {lesson.subject} · {lesson.topic}
        </p>
        <h1>{lesson.title}</h1>
        <p>Read, listen, and learn each concept at your own pace in English.</p>
        <div className="action-row">
          <Button
            onClick={() => speakText(narration)}
            disabled={!speechSupported()}
            id="btn-listen-lesson"
          >
            <Volume2 size={18} aria-hidden="true" />
            Listen to lesson
          </Button>
          <Button
            variant="secondary"
            onClick={() => navigate('/quiz')}
            id="btn-try-quiz"
          >
            Try the quiz <ChevronRight size={18} aria-hidden="true" />
          </Button>
        </div>
      </header>

      {content.summary && (
        <Card className="lesson-summary" id="lesson-summary-box">
          <Sparkles size={22} aria-hidden="true" />
          <p>{content.summary}</p>
        </Card>
      )}

      <div className="lesson-grid">
        <article>
          {content.key_points && content.key_points.length > 0 && (
            <section className="learning-section" aria-label="Key Ideas">
              <p className="eyebrow">KEY IDEAS</p>
              <h2>Understand the basics</h2>
              {content.key_points.map((point, index) => (
                <div className="key-point" key={point}>
                  <span aria-hidden="true">{index + 1}</span>
                  <p>{point}</p>
                </div>
              ))}
            </section>
          )}

          {content.try_it && (
            <Card className="try-it" id="lesson-try-it">
              <p className="eyebrow">TRY IT</p>
              <h2>Explore it yourself</h2>
              <p>{content.try_it}</p>
            </Card>
          )}
        </article>

        <aside>
          {content.vocabulary && Object.keys(content.vocabulary).length > 0 && (
            <Card id="lesson-vocab">
              <p className="eyebrow">VOCABULARY</p>
              {Object.entries(content.vocabulary).map(([term, definition]) => (
                <dl className="vocab" key={term}>
                  <dt>{term}</dt>
                  <dd>{definition}</dd>
                </dl>
              ))}
            </Card>
          )}

          {content.quiz_ready_facts && content.quiz_ready_facts.length > 0 && (
            <Card className="remember" id="lesson-remember">
              <p className="eyebrow">REMEMBER THIS</p>
              {content.quiz_ready_facts.map(fact => (
                <p key={fact}>
                  <Star size={15} aria-hidden="true" />
                  {fact}
                </p>
              ))}
            </Card>
          )}
        </aside>
      </div>

      <Card className="voice-cta" id="lesson-voice-cta">
        <div>
          <Mic aria-hidden="true" />
          <div>
            <b>Have questions about this lesson?</b>
            <p>Use your microphone or type your question in English at any time.</p>
          </div>
        </div>
        <Button
          variant="secondary"
          onClick={() => navigate('/voice')}
          id="btn-ask-voice-cta"
        >
          Ask with voice
        </Button>
      </Card>
    </Page>
  )
}
