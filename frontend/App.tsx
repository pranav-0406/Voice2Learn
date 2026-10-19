import { Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { useLearner } from './hooks/useLearner'
import { Layout } from './components/layout/Layout'
import Welcome from './pages/Welcome'
import Dashboard from './pages/Dashboard'
import LessonPage from './pages/Lesson'
import VoiceInterface from './pages/VoiceInterface'
import Quiz from './pages/Quiz'
import ProgressPage from './pages/Progress'
import type { Learner } from './types'

function AuthenticatedRoutes({
  learner,
  onLogout,
}: {
  learner: Learner
  onLogout: () => void
}) {
  return (
    <Layout learner={learner} onLogout={onLogout}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard learner={learner} />} />
        <Route path="/lesson/:lessonId" element={<LessonPage />} />
        <Route path="/voice" element={<VoiceInterface learner={learner} />} />
        <Route path="/quiz" element={<Quiz learner={learner} />} />
        <Route path="/progress" element={<ProgressPage learner={learner} />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Layout>
  )
}

export default function App() {
  const { learner, setLearner, logout } = useLearner()
  const navigate = useNavigate()

  function handleLearnerCreated(l: Learner) {
    setLearner(l)
    navigate('/dashboard')
  }

  function handleLogout() {
    logout()
    navigate('/', { replace: true })
  }

  if (!learner) {
    return (
      <Routes>
        <Route path="*" element={<Welcome onLearnerCreated={handleLearnerCreated} />} />
      </Routes>
    )
  }

  return <AuthenticatedRoutes learner={learner} onLogout={handleLogout} />
}
