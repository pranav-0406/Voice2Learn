import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Flame, Star, Target } from 'lucide-react'
import {
  Card,
  DashboardSkeleton,
  Page,
  PageError,
  Stat,
} from '../components/ui'
import { getProgress } from '../api'
import type { Difficulty, Learner, Progress } from '../types'

const difficultyLabels: Record<Difficulty, string> = {
  easy: 'Foundation',
  medium: 'Growing',
  hard: 'Advanced',
}

export function ProgressView({ learner }: { learner: Learner }) {
  const [progress, setProgress] = useState<Progress | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    getProgress(learner.id)
      .then(value => {
        if (alive) setProgress(value)
      })
      .catch(cause => {
        if (alive) {
          setError(
            cause instanceof Error ? cause.message : 'Unable to load progress statistics.'
          )
        }
      })
    return () => {
      alive = false
    }
  }, [learner.id])

  if (error) return <PageError message={error} />
  if (!progress) {
    return (
      <Page id="progress-loading">
        <DashboardSkeleton />
      </Page>
    )
  }

  return (
    <Page id="progress-view">
      <header className="page-header">
        <p className="eyebrow">LEARNING PROGRESS</p>
        <h1>See your growth, {learner.nickname}.</h1>
        <p>Your adaptive learning profile updates automatically with every quiz question.</p>
      </header>

      <div className="stat-grid" role="region" aria-label="Progress summary">
        <Stat
          icon={<Star aria-hidden="true" />}
          label="Total points"
          value={progress.points}
        />
        <Stat
          icon={<Flame aria-hidden="true" />}
          label="Correct streak"
          value={progress.correct_streak}
        />
        <Stat
          icon={<Target aria-hidden="true" />}
          label="Current level"
          value={difficultyLabels[progress.target_difficulty] || 'Foundation'}
        />
      </div>

      <Card className="mastery" id="topic-mastery-card">
        <p className="eyebrow">TOPIC MASTERY</p>
        <h2>Subject Knowledge</h2>
        {progress.topics.length > 0 ? (
          <div className="topic-mastery-list">
            {progress.topics.map(topic => (
              <div className="mastery-row" key={topic.topic}>
                <div>
                  <b>{topic.topic}</b>
                  <small>
                    {topic.correct_answers} of {topic.attempts} correct answers
                  </small>
                </div>
                <strong>{topic.mastery_percent}%</strong>
                <div
                  className="progress-track"
                  role="progressbar"
                  aria-label={`${topic.topic} mastery`}
                  aria-valuenow={topic.mastery_percent}
                  aria-valuemin={0}
                  aria-valuemax={100}
                >
                  <motion.i
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(100, topic.mastery_percent)}%` }}
                    transition={{ duration: 0.5, ease: 'easeOut' }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty compact">
            <Target size={25} aria-hidden="true" />
            <h2>Your first quiz starts here.</h2>
            <p>Answer questions in any subject to build your topic mastery.</p>
          </div>
        )}
      </Card>

      {progress.lessons && progress.lessons.length > 0 && (
        <Card className="lesson-progress" id="lesson-mastery-card">
          <p className="eyebrow">BY LESSON</p>
          <h2>Lesson Breakdown</h2>
          <div className="lesson-mastery-list">
            {progress.lessons.map(item => (
              <div key={item.lesson_id} className="lesson-mastery-item">
                <span>{item.lesson_id.replace(/-/g, ' ')}</span>
                <b>{item.mastery_percent}%</b>
              </div>
            ))}
          </div>
        </Card>
      )}
    </Page>
  )
}
