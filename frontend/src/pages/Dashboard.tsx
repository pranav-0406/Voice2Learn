import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BookOpen,
  Calculator,
  ChevronRight,
  CircleHelp,
  Compass,
  Flame,
  Globe,
  Mic,
  Sparkles,
  Star,
  Target,
} from 'lucide-react'
import {
  Button,
  Card,
  DashboardSkeleton,
  Page,
  PageError,
  Stat,
} from '../components/ui'
import { getProgress, getSubjects, getActivePosition } from '../api'
import { SubjectExplorer } from '../components/curriculum/SubjectExplorer'
import type { Difficulty, Learner, Progress, Subject, LearnerPositionResponse } from '../types'

const levelLabels: Record<Difficulty, string> = {
  easy: 'Foundation',
  medium: 'Growing',
  hard: 'Advanced',
}

// Four approved Class 6 English-medium subjects with real concept IDs
export const CLASS_6_SUBJECTS = [
  {
    id: 'english',
    name: 'English',
    icon: BookOpen,
    color: 'subject-english',
    units: 3,
    description: 'Prose, Poetry, and Vocabulary',
    activeTopic: 'Sea Turtles & Grammar',
    defaultConceptId: 'eng-ch01-c01',
  },
  {
    id: 'mathematics',
    name: 'Mathematics',
    icon: Calculator,
    color: 'subject-maths',
    units: 6,
    description: 'Numbers, Algebra, Ratios & Geometry',
    activeTopic: 'Numbers & BIDMAS',
    defaultConceptId: 'math-ch01-c01',
  },
  {
    id: 'science',
    name: 'Science',
    icon: Compass,
    color: 'subject-science',
    units: 7,
    description: 'Measurements, Motion, Matter & Living World',
    activeTopic: 'Measurements & Motion',
    defaultConceptId: 'sci-ch01-c01',
  },
  {
    id: 'social-science',
    name: 'Social Science',
    icon: Globe,
    color: 'subject-social',
    units: 8,
    description: 'History, Geography, and Civics',
    activeTopic: 'What is History? & The Solar System',
    defaultConceptId: 'soc-ch01-c01',
  },
]

export function Dashboard({ learner }: { learner: Learner }) {
  const [data, setData] = useState<{ progress: Progress; subjects: Subject[] } | null>(null)
  const [activePosition, setActivePosition] = useState<LearnerPositionResponse | null>(null)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    let alive = true
    Promise.all([
      getProgress(learner.id),
      getSubjects(),
      getActivePosition(learner.id).catch(() => null),
    ])
      .then(([progress, subjects, posResp]) => {
        if (alive) {
          setData({ progress, subjects: subjects.subjects })
          if (posResp) {
            setActivePosition(posResp)
          }
        }
      })
      .catch(e => {
        if (alive) {
          setError(e instanceof Error ? e.message : 'Unable to load your dashboard.')
        }
      })
    return () => {
      alive = false
    }
  }, [learner.id])

  const greeting =
    new Date().getHours() < 12
      ? 'Good morning'
      : new Date().getHours() < 18
      ? 'Good afternoon'
      : 'Good evening'

  if (error) return <PageError message={error} />
  if (!data) {
    return (
      <Page id="dashboard-loading">
        <DashboardSkeleton />
      </Page>
    )
  }

  const { progress } = data
  const heroConceptId = activePosition?.concept_id || 'sci-ch01-c01'
  const heroChapterTitle = activePosition?.chapter_title || 'Measurement'
  const heroConceptTitle =
    activePosition?.concept_title ||
    'Explore international standard units and measuring length, mass, and time.'

  return (
    <Page id="dashboard-view">
      <header className="page-header">
        <p className="eyebrow">{greeting.toUpperCase()}</p>
        <h1>{learner.nickname}, ready to learn?</h1>
        <p>Class 6 · Tamil Nadu State Board Curriculum (English Medium)</p>
      </header>

      <div className="stat-grid" role="region" aria-label="Learning Statistics">
        <Stat
          icon={<Star aria-hidden="true" />}
          label="Points earned"
          value={progress.points}
        />
        <Stat
          icon={<Flame aria-hidden="true" />}
          label="Current streak"
          value={progress.correct_streak}
        />
        <Stat
          icon={<Target aria-hidden="true" />}
          label="Learning level"
          value={levelLabels[progress.target_difficulty] || 'Foundation'}
        />
      </div>

      <section className="hero-card" aria-labelledby="continue-learning-title">
        <div>
          <p className="eyebrow">CONTINUE LEARNING</p>
          <h2 id="continue-learning-title">{heroChapterTitle}</h2>
          <p>{heroConceptTitle}</p>
          <Button
            onClick={() => navigate(`/concept/${heroConceptId}`)}
            id="btn-continue-lesson"
          >
            Continue lesson <ChevronRight size={18} aria-hidden="true" />
          </Button>
        </div>
        <div className="hero-orb" aria-hidden="true">
          <Sparkles size={42} />
        </div>
      </section>

      <div className="content-grid">
        <Card id="quick-start-card">
          <div className="section-title">
            <div>
              <p className="eyebrow">QUICK START</p>
              <h2>Learn your way</h2>
            </div>
          </div>
          <button
            type="button"
            className="feature-link"
            onClick={() => navigate('/voice')}
            id="quick-ask-voice"
          >
            <span className="icon-box violet" aria-hidden="true">
              <Mic />
            </span>
            <span>
              <b>Ask with voice</b>
              <small>Speak or type any question in English</small>
            </span>
            <ChevronRight aria-hidden="true" />
          </button>
          <button
            type="button"
            className="feature-link"
            onClick={() => navigate('/quiz')}
            id="quick-start-quiz"
          >
            <span className="icon-box mint" aria-hidden="true">
              <CircleHelp />
            </span>
            <span>
              <b>Take adaptive quiz</b>
              <small>Questions adapt to your pace and ability</small>
            </span>
            <ChevronRight aria-hidden="true" />
          </button>
        </Card>

        <Card id="subjects-card">
          <p className="eyebrow">CLASS 6 SUBJECTS (4)</p>
          <h2>Your learning library</h2>
          <div className="subject-list" role="list">
            {CLASS_6_SUBJECTS.map(subject => {
              const Icon = subject.icon
              return (
                <button
                  type="button"
                  className="subject-row"
                  key={subject.id}
                  id={`subject-item-${subject.id}`}
                  onClick={() => navigate(`/concept/${subject.defaultConceptId}`)}
                >
                  <span className={`subject-icon-box ${subject.color}`} aria-hidden="true">
                    <Icon size={20} />
                  </span>
                  <span className="subject-text">
                    <b>{subject.name}</b>
                    <small>
                      {subject.units} Units · {subject.activeTopic}
                    </small>
                  </span>
                  <ChevronRight size={17} aria-hidden="true" />
                </button>
              )
            })}
          </div>
        </Card>
      </div>

      <SubjectExplorer />
    </Page>
  )
}
