import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Mic2, Zap, BookOpen, BarChart2, Flame, Star, TrendingUp } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Card, Badge } from '../components/ui/Card'
import { getSubjects, getProgress } from '../services/api'
import type { Learner, Subject, Progress } from '../types'

interface DashboardProps { learner: Learner }

const difficultyLabel = { easy: 'Foundation', medium: 'Intermediate', hard: 'Advanced' }
const difficultyColor = { easy: 'emerald', medium: 'amber', hard: 'violet' } as const

export default function Dashboard({ learner }: DashboardProps) {
  const navigate = useNavigate()
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [progress, setProgress] = useState<Progress | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    Promise.all([getSubjects(), getProgress(learner.id)])
      .then(([subjectData, progressData]) => {
        if (cancelled) return
        setSubjects(subjectData.subjects)
        setProgress(progressData)
      })
      .catch(err => {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Could not load dashboard data.')
      })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [learner.id])

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <p className="text-sm text-navy-700/50 font-medium mb-0.5">{greeting}</p>
        <h1 className="text-3xl font-extrabold text-navy-900 tracking-tight">{learner.nickname}</h1>
      </div>

      {/* Stats row */}
      {progress && (
        <div className="grid grid-cols-3 gap-3">
          {[
            { icon: Star, label: 'Points', value: progress.points, color: 'text-amber-500' },
            { icon: Flame, label: 'Streak', value: `${progress.correct_streak}🔥`, color: 'text-rose-500' },
            { icon: TrendingUp, label: 'Level', value: difficultyLabel[progress.target_difficulty], color: 'text-primary-600' },
          ].map(({ icon: Icon, label, value, color }) => (
            <Card key={label} className="p-4 text-center">
              <Icon className={`w-5 h-5 mx-auto mb-1 ${color}`} />
              <p className="text-xs text-navy-700/50 mb-0.5">{label}</p>
              <p className="font-bold text-navy-900 text-sm">{value}</p>
            </Card>
          ))}
        </div>
      )}

      {/* Primary CTA */}
      <motion.div
        className="rounded-3xl bg-primary-600 p-6 text-white relative overflow-hidden"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <div className="absolute top-0 right-0 w-40 h-40 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/4" />
        <p className="text-sm font-medium text-white/70 mb-1">Featured</p>
        <h2 className="text-xl font-extrabold mb-1">Science</h2>
        <p className="text-sm text-white/70 mb-4">States of Matter · Class {learner.grade_band}</p>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="secondary"
            size="md"
            onClick={() => navigate('/lesson/science-matter-basics')}
            className="bg-white text-primary-700 border-transparent hover:bg-white/90"
          >
            <BookOpen className="w-4 h-4" />
            Read Lesson
          </Button>
          <Button
            variant="secondary"
            size="md"
            onClick={() => navigate('/quiz')}
            className="bg-primary-700 text-white border-primary-700 hover:bg-primary-800"
          >
            <Zap className="w-4 h-4" />
            Start Quiz
          </Button>
        </div>
      </motion.div>

      {/* Voice card */}
      <Card
        hover
        onClick={() => navigate('/voice')}
        className="p-5 flex items-center gap-4"
      >
        <div className="w-12 h-12 rounded-2xl bg-violet-600/10 flex items-center justify-center shrink-0">
          <Mic2 className="w-6 h-6 text-violet-600" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-bold text-navy-900 text-sm">Ask with your voice</p>
          <p className="text-xs text-navy-700/50 mt-0.5">Speak your Science question out loud</p>
        </div>
        <Badge color="violet">Voice</Badge>
      </Card>

      {/* Subjects */}
      {loading ? (
        <div className="space-y-3">
          {[0, 1].map(i => (
            <div key={i} className="h-16 rounded-2xl bg-base-100 animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <p className="text-sm text-rose-500">{error}</p>
      ) : (
        <div>
          <h2 className="text-sm font-bold text-navy-700/50 uppercase tracking-wide mb-3">Subjects</h2>
          <div className="space-y-2">
            {subjects.map(subject => (
              <Card
                key={subject.id}
                hover
                onClick={() => navigate('/lesson/science-matter-basics')}
                className="p-4 flex items-center gap-4"
              >
                <BookOpen className="w-5 h-5 text-primary-600 shrink-0" />
                <div className="flex-1">
                  <p className="font-semibold text-navy-900 text-sm">{subject.name}</p>
                  <p className="text-xs text-navy-700/50">{subject.language}</p>
                </div>
                {progress && progress.topics.length > 0 && (
                  <Badge color={difficultyColor[progress.target_difficulty]}>
                    {difficultyLabel[progress.target_difficulty]}
                  </Badge>
                )}
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Progress entry */}
      <Card hover onClick={() => navigate('/progress')} className="p-4 flex items-center gap-4">
        <BarChart2 className="w-5 h-5 text-emerald-500 shrink-0" />
        <div className="flex-1">
          <p className="font-semibold text-navy-900 text-sm">My Progress</p>
          <p className="text-xs text-navy-700/50">
            {progress && progress.topics.length > 0
              ? `${progress.topics.length} topic${progress.topics.length !== 1 ? 's' : ''} studied`
              : 'No quizzes completed yet'}
          </p>
        </div>
      </Card>
    </div>
  )
}
