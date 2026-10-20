import { useState } from 'react'
import { Check, Delete, KeyRound, Lock, LogIn, Sparkles, User, UserPlus } from 'lucide-react'
import { loginStudent, registerStudent } from '../../api'
import type { GradeBand, StudentProfile } from '../../types'

interface AuthModalProps {
  onSuccess: (student: StudentProfile) => void
  initialMode?: 'login' | 'register'
}

export function AuthModal({ onSuccess, initialMode = 'login' }: AuthModalProps) {
  const [mode, setMode] = useState<'login' | 'register'>(initialMode)
  const [nickname, setNickname] = useState('')
  const [pin, setPin] = useState('')
  const [gradeBand, setGradeBand] = useState<GradeBand>('6-7')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleKeypadPress = (digit: string) => {
    if (pin.length < 6) {
      setPin((prev) => prev + digit)
      setError(null)
    }
  }

  const handleKeypadBackspace = () => {
    setPin((prev) => prev.slice(0, -1))
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!nickname.trim()) {
      setError('Please enter your nickname')
      return
    }
    if (pin.length < 4) {
      setError('Please enter at least a 4-digit PIN')
      return
    }

    setLoading(true)
    try {
      if (mode === 'register') {
        const res = await registerStudent(nickname.trim(), pin, gradeBand)
        onSuccess(res.student)
      } else {
        const res = await loginStudent(nickname.trim(), pin)
        onSuccess(res.student)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card auth-card" id="auth-modal">
      <div className="auth-tabs" role="tablist" aria-label="Sign in options">
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'login'}
          className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
          id="tab-auth-login"
          onClick={() => {
            setMode('login')
            setError(null)
          }}
        >
          <LogIn size={16} aria-hidden="true" />
          <span>Sign In</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'register'}
          className={`auth-tab ${mode === 'register' ? 'active' : ''}`}
          id="tab-auth-register"
          onClick={() => {
            setMode('register')
            setError(null)
          }}
        >
          <UserPlus size={16} aria-hidden="true" />
          <span>New Student</span>
        </button>
      </div>

      <header className="auth-header">
        <p className="eyebrow">
          {mode === 'login' ? 'WELCOME BACK' : 'START LEARNING'}
        </p>
        <h2>{mode === 'login' ? 'Sign in to Voice2Learn' : 'Create your student profile'}</h2>
        <p className="muted">
          Class 6 · Tamil Nadu State Board (English-medium)
        </p>
      </header>

      {error && (
        <div className="notice error" role="alert" id="auth-error-msg">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="auth-form" noValidate>
        <div className="form-group">
          <label htmlFor="auth-nickname">
            <User size={15} aria-hidden="true" />
            <span>Student Nickname</span>
          </label>
          <input
            id="auth-nickname"
            type="text"
            className="input-field"
            placeholder="e.g. Santhosh"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            disabled={loading}
            autoFocus
            required
          />
        </div>

        {mode === 'register' && (
          <fieldset className="grade-band-fieldset">
            <legend className="form-label">Select Grade</legend>
            <div className="grade-options">
              <label className={gradeBand === '6-7' ? 'selected' : ''}>
                <input
                  type="radio"
                  name="grade_band"
                  value="6-7"
                  checked={gradeBand === '6-7'}
                  onChange={() => setGradeBand('6-7')}
                />
                Class 6 (Ages 11–12)
              </label>
              <label className={gradeBand === '8-9' ? 'selected' : ''}>
                <input
                  type="radio"
                  name="grade_band"
                  value="8-9"
                  checked={gradeBand === '8-9'}
                  onChange={() => setGradeBand('8-9')}
                />
                Class 7 (Ages 12–13)
              </label>
            </div>
          </fieldset>
        )}

        <div className="form-group">
          <label htmlFor="auth-pin">
            <KeyRound size={15} aria-hidden="true" />
            <span>4-Digit Secret PIN</span>
          </label>
          <div className="pin-display-row">
            <input
              id="auth-pin"
              type="password"
              className="input-field pin-input"
              maxLength={6}
              placeholder="••••"
              value={pin}
              onChange={(e) => setPin(e.target.value.replace(/\D/g, ''))}
              disabled={loading}
              inputMode="numeric"
            />
          </div>

          {/* Accessible Large On-Screen Keypad for mobility/touch students */}
          <div className="pin-keypad" role="group" aria-label="PIN numeric keypad">
            {['1', '2', '3', '4', '5', '6', '7', '8', '9'].map((digit) => (
              <button
                key={digit}
                type="button"
                className="keypad-btn"
                id={`keypad-${digit}`}
                onClick={() => handleKeypadPress(digit)}
                disabled={loading}
              >
                {digit}
              </button>
            ))}
            <button
              type="button"
              className="keypad-btn action"
              onClick={handleKeypadBackspace}
              disabled={loading || pin.length === 0}
              aria-label="Delete digit"
            >
              <Delete size={18} />
            </button>
            <button
              type="button"
              className="keypad-btn"
              id="keypad-0"
              onClick={() => handleKeypadPress('0')}
              disabled={loading}
            >
              0
            </button>
            <button
              type="submit"
              className="keypad-btn submit"
              disabled={loading || pin.length < 4}
              aria-label="Submit PIN"
            >
              <Check size={20} />
            </button>
          </div>
        </div>

        <button
          type="submit"
          className="button primary full-width"
          id="btn-auth-submit"
          disabled={loading || !nickname.trim() || pin.length < 4}
        >
          {loading ? (
            <span className="spinner" />
          ) : mode === 'login' ? (
            <>
              Sign In <Lock size={16} aria-hidden="true" />
            </>
          ) : (
            <>
              Start Learning <Sparkles size={16} aria-hidden="true" />
            </>
          )}
        </button>
      </form>
    </div>
  )
}
