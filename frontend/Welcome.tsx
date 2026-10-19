import { useState } from 'react'
import { motion } from 'framer-motion'
import { Mic2, ChevronRight } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { createLearner } from '../services/api'
import type { GradeBand, Learner } from '../types'

interface WelcomeProps {
  onLearnerCreated: (learner: Learner) => void
}

export default function Welcome({ onLearnerCreated }: WelcomeProps) {
  const [nickname, setNickname] = useState('')
  const [gradeBand, setGradeBand] = useState<GradeBand>('6-7')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const name = nickname.trim()
    if (!name) { setError('Please enter your name.'); return }
    setLoading(true)
    setError(null)
    try {
      const learner = await createLearner(name, gradeBand)
      onLearnerCreated(learner)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not connect to the server. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-base-50 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Logo */}
        <motion.div
          className="flex flex-col items-center mb-10"
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        >
          <div className="w-16 h-16 rounded-2xl bg-primary-600 flex items-center justify-center mb-4 shadow-glow">
            <Mic2 className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-extrabold text-navy-900 tracking-tight mb-1">Voice2Learn</h1>
          <p className="text-navy-700/60 text-sm text-center max-w-xs text-balance">
            Learn Science through your voice — ask questions, take quizzes, and track your progress.
          </p>
        </motion.div>

        {/* Form card */}
        <motion.div
          className="bg-white rounded-3xl border border-base-200 shadow-card p-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1, ease: 'easeOut' }}
        >
          <h2 className="text-xl font-bold text-navy-900 mb-1">Get started</h2>
          <p className="text-sm text-navy-700/60 mb-6">Just your name and class — nothing else.</p>

          <form onSubmit={handleSubmit} noValidate>
            <div className="space-y-5">
              {/* Name */}
              <div>
                <label htmlFor="nickname" className="block text-sm font-semibold text-navy-900 mb-1.5">
                  Your name
                </label>
                <input
                  id="nickname"
                  type="text"
                  autoComplete="off"
                  autoFocus
                  value={nickname}
                  onChange={e => setNickname(e.target.value)}
                  maxLength={40}
                  placeholder="e.g. Asha"
                  className="w-full h-12 px-4 rounded-xl border border-base-200 bg-base-50 text-navy-900 placeholder-navy-700/30 text-sm font-medium
                    focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-shadow duration-150"
                  aria-required="true"
                />
              </div>

              {/* Grade band */}
              <div>
                <span className="block text-sm font-semibold text-navy-900 mb-2">Your class</span>
                <div className="grid grid-cols-2 gap-3" role="radiogroup" aria-label="Grade band">
                  {(['6-7', '8-9'] as GradeBand[]).map(band => (
                    <label
                      key={band}
                      className={[
                        'flex items-center justify-center h-12 rounded-xl border text-sm font-semibold cursor-pointer transition-colors duration-150',
                        gradeBand === band
                          ? 'bg-primary-600 border-primary-600 text-white shadow-glow'
                          : 'bg-white border-base-200 text-navy-700 hover:border-primary-300',
                      ].join(' ')}
                    >
                      <input
                        type="radio"
                        name="gradeBand"
                        value={band}
                        checked={gradeBand === band}
                        onChange={() => setGradeBand(band)}
                        className="sr-only"
                      />
                      Class {band}
                    </label>
                  ))}
                </div>
              </div>

              {/* Error */}
              {error && (
                <p role="alert" className="text-sm text-rose-500 font-medium">
                  {error}
                </p>
              )}

              <Button type="submit" size="xl" fullWidth loading={loading} className="mt-2">
                Start Learning
                <ChevronRight className="w-5 h-5" />
              </Button>
            </div>
          </form>
        </motion.div>

        {/* How it works */}
        <motion.div
          className="mt-8 grid grid-cols-3 gap-4 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.25 }}
        >
          {[
            { emoji: '🎙️', title: 'Speak', desc: 'Ask any Science question aloud' },
            { emoji: '📖', title: 'Learn', desc: 'Read lessons and take quizzes' },
            { emoji: '📈', title: 'Grow', desc: 'Track your progress over time' },
          ].map(({ emoji, title, desc }) => (
            <div key={title} className="px-2">
              <div className="text-2xl mb-1.5">{emoji}</div>
              <p className="text-xs font-bold text-navy-900 mb-0.5">{title}</p>
              <p className="text-xs text-navy-700/50 leading-snug">{desc}</p>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  )
}
