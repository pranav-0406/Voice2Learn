import { motion } from 'framer-motion'
import { Check } from 'lucide-react'
import { Brand } from '../components/layout/Navbar'
import { AuthModal } from '../components/auth/AuthModal'
import type { Learner } from '../types'

export function Welcome({ onReady }: { onReady: (learner: Learner) => void }) {
  return (
    <main className="welcome">
      <div className="welcome-copy">
        <Brand />
        <p className="eyebrow">VOICE-FIRST LEARNING PLATFORM</p>
        <h1>
          Learning that moves at <em>your</em> pace.
        </h1>
        <p>
          Master Class 6 English, Mathematics, Science, and Social Science with voice-enabled lessons and adaptive quizzes.
        </p>
        <div className="benefits">
          <span>
            <Check aria-hidden="true" />
            Built for keyboard, touch, and voice
          </span>
          <span>
            <Check aria-hidden="true" />
            Clear English audio explanations
          </span>
          <span>
            <Check aria-hidden="true" />
            Tamil Nadu State Board syllabus
          </span>
        </div>
      </div>

      <motion.section
        className="auth-section"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <AuthModal onSuccess={onReady} />
      </motion.section>
    </main>
  )
}
