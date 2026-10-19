import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Mic2, Zap, ChevronRight, BookOpen } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Card, Badge } from '../components/ui/Card'
import { getLesson } from '../services/api'
import type { Lesson } from '../types'

export default function LessonPage() {
  const { lessonId } = useParams<{ lessonId: string }>()
  const navigate = useNavigate()
  const [lesson, setLesson] = useState<Lesson | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!lessonId) return
    setLoading(true)
    getLesson(lessonId)
      .then(setLesson)
      .catch(err => setError(err instanceof Error ? err.message : 'Lesson not found.'))
      .finally(() => setLoading(false))
  }, [lessonId])

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 w-48 bg-base-200 rounded-xl" />
        <div className="h-4 w-32 bg-base-100 rounded-xl" />
        <div className="h-40 bg-base-100 rounded-2xl" />
        <div className="h-40 bg-base-100 rounded-2xl" />
      </div>
    )
  }

  if (error || !lesson) {
    return (
      <div className="text-center py-16">
        <p className="text-navy-700/50 mb-4">{error ?? 'Lesson not found.'}</p>
        <Button variant="secondary" onClick={() => navigate('/dashboard')}>Back to Dashboard</Button>
      </div>
    )
  }

  const { content } = lesson

  return (
    <div className="space-y-7">
      {/* Header */}
      <div>
        <Badge color="indigo" className="mb-3">
          <BookOpen className="w-3 h-3" /> {lesson.subject}
        </Badge>
        <h1 className="text-3xl font-extrabold text-navy-900 tracking-tight mb-1">{lesson.title}</h1>
        <p className="text-sm text-navy-700/50">{lesson.topic}</p>
      </div>

      {/* Summary */}
      {content.summary && (
        <motion.div
          className="p-5 rounded-2xl bg-primary-600/6 border border-primary-600/12"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.05 }}
        >
          <p className="text-sm font-medium text-navy-900 leading-relaxed">{content.summary}</p>
        </motion.div>
      )}

      {/* Key points */}
      {Array.isArray(content.key_points) && content.key_points.length > 0 && (
        <div>
          <h2 className="text-sm font-bold text-navy-700/50 uppercase tracking-wide mb-3">Key Points</h2>
          <ul className="space-y-2">
            {content.key_points.map((point: string, i: number) => (
              <li
                key={i}
                className="flex items-start gap-3 p-4 bg-white rounded-xl border border-base-200 shadow-card text-sm text-navy-900 leading-relaxed"
              >
                <span className="w-6 h-6 rounded-full bg-primary-600/10 text-primary-700 text-xs font-bold flex items-center justify-center shrink-0 mt-px">
                  {i + 1}
                </span>
                {point}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Vocabulary */}
      {content.vocabulary && Object.keys(content.vocabulary).length > 0 && (
        <div>
          <h2 className="text-sm font-bold text-navy-700/50 uppercase tracking-wide mb-3">Vocabulary</h2>
          <Card className="divide-y divide-base-100">
            {Object.entries(content.vocabulary as Record<string, string>).map(([term, def]) => (
              <div key={term} className="px-4 py-3">
                <span className="font-semibold text-sm text-navy-900 capitalize">{term}</span>
                <span className="mx-2 text-navy-700/30">—</span>
                <span className="text-sm text-navy-700/70">{def}</span>
              </div>
            ))}
          </Card>
        </div>
      )}

      {/* Try it */}
      {content.try_it && (
        <Card className="p-5 border-l-4 border-l-emerald-500">
          <p className="text-xs font-bold text-emerald-500 uppercase tracking-wide mb-1.5">Try It</p>
          <p className="text-sm text-navy-900 leading-relaxed">{content.try_it}</p>
        </Card>
      )}

      {/* Quiz ready facts */}
      {Array.isArray(content.quiz_ready_facts) && content.quiz_ready_facts.length > 0 && (
        <div>
          <h2 className="text-sm font-bold text-navy-700/50 uppercase tracking-wide mb-3">Remember This</h2>
          <ul className="space-y-2">
            {content.quiz_ready_facts.map((fact: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-sm text-navy-900">
                <span className="text-amber-500 mt-0.5 shrink-0">★</span>
                {fact}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap gap-3 pt-2">
        <Button size="lg" onClick={() => navigate('/quiz')} className="flex-1 min-w-[160px]">
          <Zap className="w-5 h-5" />
          Start Quiz
          <ChevronRight className="w-4 h-4 ml-auto" />
        </Button>
        <Button variant="secondary" size="lg" onClick={() => navigate('/voice')} className="flex-1 min-w-[160px]">
          <Mic2 className="w-5 h-5" />
          Ask a Question
        </Button>
      </div>
    </div>
  )
}
