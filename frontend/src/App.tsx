import { useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { AnimatePresence, MotionConfig } from 'framer-motion'

import { Navbar, MobileNav } from './components/layout/Navbar'
import { VoiceStatusBar } from './components/voice/VoiceStatusBar'
import { Welcome } from './pages/Welcome'
import { Dashboard } from './pages/Dashboard'
import { LessonView } from './pages/LessonView'
import { ConceptViewer } from './pages/ConceptViewer'
import { VoiceView } from './pages/VoiceView'
import { QuizView } from './pages/QuizView'
import { ProgressView } from './pages/ProgressView'
import { logoutStudent } from './api'
import type { Learner } from './types'
import { VoiceProvider } from './voice'

// ─── Storage helpers ─────────────────────────────────────────────────────────

function loadLearner(): Learner | null {
  try {
    return JSON.parse(localStorage.getItem('v2l-learner') || 'null')
  } catch {
    return null
  }
}

function saveLearner(learner: Learner) {
  localStorage.setItem('v2l-learner', JSON.stringify(learner))
}

function removeLearner() {
  localStorage.removeItem('v2l-learner')
}

// ─── Authenticated shell ──────────────────────────────────────────────────────

function AuthenticatedShell({
  learner,
  onLogout,
  highContrast,
  onToggleHighContrast,
}: {
  learner: Learner
  onLogout: () => void
  highContrast: boolean
  onToggleHighContrast: () => void
}) {
  return (
    <div className={`app-shell ${highContrast ? 'high-contrast' : ''}`}>
      <Navbar
        learner={learner}
        onLogout={onLogout}
        highContrast={highContrast}
        onToggleHighContrast={onToggleHighContrast}
      />

      <main className="main-content" id="main-content" tabIndex={-1}>
        <AnimatePresence mode="wait">
          <Routes>
            <Route path="/dashboard" element={<Dashboard learner={learner} />} />
            <Route path="/lesson/:id" element={<LessonView />} />
            <Route path="/concept/:conceptId" element={<ConceptViewer />} />
            <Route path="/voice" element={<VoiceView />} />
            <Route path="/quiz" element={<QuizView learner={learner} />} />
            <Route path="/progress" element={<ProgressView learner={learner} />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </AnimatePresence>
      </main>

      {/* Persistent voice control bar — always accessible from all screens */}
      <VoiceStatusBar />

      {/* Mobile bottom nav */}
      <MobileNav />
    </div>
  )
}

// ─── Root shell ───────────────────────────────────────────────────────────────

function Shell() {
  const [learner, setLearner] = useState<Learner | null>(loadLearner)
  const [highContrast, setHighContrast] = useState(false)
  const navigate = useNavigate()

  function handleLearnerReady(l: Learner) {
    saveLearner(l)
    setLearner(l)
    navigate('/dashboard', { replace: true })
  }

  function handleLogout() {
    window.dispatchEvent(new Event('voice-stop'))
    logoutStudent()
    removeLearner()
    setLearner(null)
    navigate('/', { replace: true })
  }

  if (!learner) {
    return (
      <Routes>
        <Route path="*" element={<Welcome onReady={handleLearnerReady} />} />
      </Routes>
    )
  }

  return (
    <AuthenticatedShell
      learner={learner}
      onLogout={handleLogout}
      highContrast={highContrast}
      onToggleHighContrast={() => setHighContrast(v => !v)}
    />
  )
}

// ─── App root ─────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <BrowserRouter>
      <VoiceProvider>
        <MotionConfig reducedMotion="user">
          <Shell />
        </MotionConfig>
      </VoiceProvider>
    </BrowserRouter>
  )
}
