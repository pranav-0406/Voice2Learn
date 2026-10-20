import { NavLink } from 'react-router-dom'
import {
  BarChart3,
  BookOpen,
  CircleHelp,
  Home,
  LogOut,
  Mic,
  Moon,
  Sun,
} from 'lucide-react'
import type { Learner } from '../../types'

export const DEFAULT_CONCEPT_ID = 'sci-ch01-c01'
export const DEFAULT_LESSON_ID = 'science-measurements'

export const routeItems = [
  { to: '/dashboard', label: 'Home', icon: Home, id: 'nav-home' },
  { to: `/concept/${DEFAULT_CONCEPT_ID}`, label: 'Lesson', icon: BookOpen, id: 'nav-lesson' },
  { to: '/quiz', label: 'Quiz', icon: CircleHelp, id: 'nav-quiz' },
  { to: '/voice', label: 'Voice Assistant', icon: Mic, id: 'nav-voice' },
  { to: '/progress', label: 'Progress', icon: BarChart3, id: 'nav-progress' },
]

export function Brand() {
  return (
    <div className="brand" id="brand-logo">
      <span className="brand-mark" aria-hidden="true">
        <Mic size={20} />
      </span>
      <span>
        Voice<span>2</span>Learn
      </span>
    </div>
  )
}

export function Navbar({
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
    <aside className="side-nav" aria-label="Main Navigation">
      <Brand />

      <nav aria-label="Sidebar Links">
        {routeItems.map(({ to, label, icon: Icon, id }) => (
          <NavLink
            key={to}
            to={to}
            id={id}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <Icon size={19} aria-hidden="true" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="nav-accessibility">
        <button
          type="button"
          className="button quiet a11y-toggle"
          onClick={onToggleHighContrast}
          aria-label={highContrast ? 'Switch to standard contrast' : 'Switch to high contrast'}
          title={highContrast ? 'Standard contrast mode' : 'High contrast mode'}
        >
          {highContrast ? <Sun size={17} /> : <Moon size={17} />}
          <span>{highContrast ? 'Standard Mode' : 'High Contrast'}</span>
        </button>
      </div>

      <div className="nav-footer">
        <span className="avatar" aria-hidden="true">
          {learner.nickname[0]?.toUpperCase()}
        </span>
        <span className="learner-info">
          <b>{learner.nickname}</b>
          <small>Class {learner.grade_band}</small>
        </span>
        <button
          type="button"
          aria-label="Sign out of Voice2Learn"
          onClick={onLogout}
          title="Sign out"
          className="logout-button"
        >
          <LogOut size={18} aria-hidden="true" />
        </button>
      </div>
    </aside>
  )
}

export function MobileNav() {
  return (
    <nav className="mobile-nav" aria-label="Mobile Navigation">
      {routeItems.map(({ to, label, icon: Icon, id }) => (
        <NavLink
          key={to}
          to={to}
          id={`mobile-${id}`}
          className={({ isActive }) => (isActive ? 'active' : '')}
        >
          <Icon size={20} aria-hidden="true" />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
