import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Star, Flame, TrendingUp, BookOpen, Target } from 'lucide-react'
import { Card, Badge } from '../components/ui/Card'
import { getProgress } from '../services/api'
import type { Learner, Progress } from '../types'

interface ProgressPageProps { learner: Learner }

const difficultyLabel = { easy: 'Foundation', medium: 'Intermediate', hard: 'Advanced' }
const difficultyColor = { easy: 'emerald', medium: 'amber', hard: 'violet' } as const

function MasteryBar({ percent, color }: { percent: number; color: string }) {
  return (
    <div className="h-2 bg-base-100 rounded-full overflow-hidden" role="progressbar" aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100}>
      <motion.div
        className={`h-full rounded-full ${color}`}
        initial={{ width: 0 }}
        animate={{ width: `${Math.min(100, percent)}%` }}
        transition={{ duration: 0.8, ease: 'easeOut', delay: 0.2 }}
      />
    </div>
  )
}

export default function ProgressPage({ learner }: ProgressPageProps) {
  const [progress, setProgress] = useState<Progress | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getProgress(learner.id)
      .then(setProgress)
      .catch(err => setError(err instanceof Error ? err.message : 'Could not load progress.'))
      .finally(() => setLoading(false))
  }, [learner.id])

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 w-40 bg-base-200 rounded-xl" />
        <div className="grid grid-cols-3 gap-3">
          {[0, 1, 2].map(i => <div key={i} className="h-24 bg-base-100 rounded-2xl" />)}
        </div>
        <div className="h-48 bg-base-100 rounded-2xl" />
      </div>
    )
  }

  if (error) {
    return <p className="text-sm text-rose-500 py-8 text-center">{error}</p>
  }

  if (!progress) return null

  const hasActivity = progress.topics.length > 0

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-navy-900 tracking-tight mb-1">My Progress</h1>
        <p className="text-sm text-navy-700/50">{learner.nickname} · Class {learner.grade_band}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3">
        {[
          { icon: Star, label: 'Total Points', value: progress.points, color: 'text-amber-500', bg: 'bg-amber-50' },
          { icon: Flame, label: 'Correct Streak', value: progress.correct_streak, color: 'text-rose-500', bg: 'bg-rose-50' },
          { icon: TrendingUp, label: 'Ability Score', value: Math.round(progress.ability), color: 'text-primary-600', bg: 'bg-primary-50' },
          { icon: Target, label: 'Current Level', value: difficultyLabel[progress.target_difficulty], color: 'text-violet-600', bg: 'bg-violet-50' },
        ].map(({ icon: Icon, label, value, color, bg }) => (
          <Card key={label} className={`p-4 ${bg} border-transparent`}>
            <Icon className={`w-5 h-5 mb-2 ${color}`} />
            <p className="text-xs text-navy-700/50 mb-0.5">{label}</p>
            <p className="font-extrabold text-navy-900">{value}</p>
          </Card>
        ))}
      </div>

      {/* Level badge */}
      <div className="flex items-center gap-3">
        <Badge color={difficultyColor[progress.target_difficulty]} className="text-sm px-3 py-1">
          <TrendingUp className="w-3.5 h-3.5" />
          {difficultyLabel[progress.target_difficulty]} level
        </Badge>
        {progress.incorrect_streak >= 1 && (
          <p className="text-xs text-navy-700/40">{progress.incorrect_streak} incorrect in a row — keep going!</p>
        )}
      </div>

      {/* Topic mastery */}
      <div>
        <h2 className="text-sm font-bold text-navy-700/50 uppercase tracking-wide mb-4">Topic Mastery</h2>
        {hasActivity ? (
          <div className="space-y-4">
            {progress.topics.map(topic => (
              <Card key={topic.topic} className="p-5">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-primary-600 shrink-0" />
                    <p className="font-semibold text-sm text-navy-900">{topic.topic}</p>
                  </div>
                  <p className="text-sm font-bold text-navy-900">{topic.mastery_percent}%</p>
                </div>
                <MasteryBar
                  percent={topic.mastery_percent}
                  color={topic.mastery_percent >= 80 ? 'bg-emerald-500' : topic.mastery_percent >= 50 ? 'bg-amber-400' : 'bg-primary-400'}
                />
                <p className="text-xs text-navy-700/40 mt-2">
                  {topic.correct_answers} of {topic.attempts} correct
                </p>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="p-8 text-center">
            <Target className="w-8 h-8 text-navy-700/20 mx-auto mb-2" />
            <p className="font-semibold text-navy-900 mb-1">No quizzes yet</p>
            <p className="text-sm text-navy-700/50">Complete your first quiz to see progress here.</p>
          </Card>
        )}
      </div>

      {/* Lesson progress */}
      {progress.lessons.length > 0 && (
        <div>
          <h2 className="text-sm font-bold text-navy-700/50 uppercase tracking-wide mb-4">By Lesson</h2>
          <div className="space-y-3">
            {progress.lessons.map(lesson => (
              <Card key={lesson.lesson_id} className="px-4 py-3 flex items-center gap-4">
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-navy-700/50 truncate">{lesson.lesson_id.replace(/-/g, ' ')}</p>
                  <p className="text-sm font-semibold text-navy-900">
                    {lesson.correct_answers}/{lesson.attempts} correct
                  </p>
                </div>
                <p className="text-sm font-extrabold text-navy-900 shrink-0">{lesson.mastery_percent}%</p>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
