import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { LucideIcon } from 'lucide-react'
import {
  BookOpen,
  Calculator,
  ChevronRight,
  CircleHelp,
  Compass,
  FileText,
  Globe,
  GraduationCap,
  Sparkles,
  PlayCircle,
} from 'lucide-react'
import { fetchCurriculumSubjects, fetchTermChapters, fetchChapterDetail } from '../../api'
import type { CurriculumChapter, CurriculumSubject } from '../../types'

interface SubjectExplorerProps {
  onSelectLesson?: (lessonId: string) => void
}

const ICON_MAP: Record<string, LucideIcon> = {
  BookOpen,
  Calculator,
  Compass,
  Globe,
  Atom: Compass,
}

export function SubjectExplorer({ onSelectLesson }: SubjectExplorerProps) {
  const [subjects, setSubjects] = useState<CurriculumSubject[]>([])
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('science')
  const [chapters, setChapters] = useState<CurriculumChapter[]>([])
  const [loadingChapters, setLoadingChapters] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const navigate = useNavigate()

  useEffect(() => {
    let alive = true
    fetchCurriculumSubjects()
      .then((subs) => {
        if (!alive) return
        setSubjects(subs)
        if (subs.length > 0) {
          // Default to science or first subject
          const defaultSubj = subs.find((s) => s.id === 'science') || subs[0]
          setSelectedSubjectId(defaultSubj.id)
        }
      })
      .catch((err) => {
        if (alive) setError(err instanceof Error ? err.message : 'Could not load subjects')
      })

    return () => {
      alive = false
    }
  }, [])

  useEffect(() => {
    if (!selectedSubjectId) return
    let alive = true
    setLoadingChapters(true)
    fetchTermChapters(selectedSubjectId, 1)
      .then((chaps) => {
        if (alive) {
          setChapters(chaps)
        }
      })
      .catch((err) => {
        if (alive) setError(err instanceof Error ? err.message : 'Could not load chapters')
      })
      .finally(() => {
        if (alive) setLoadingChapters(false)
      })

    return () => {
      alive = false
    }
  }, [selectedSubjectId])

  const currentSubject = subjects.find((s) => s.id === selectedSubjectId)

  return (
    <section className="card curriculum-explorer" aria-labelledby="curriculum-title" id="curriculum-explorer-section">
      <div className="curriculum-header">
        <div>
          <p className="eyebrow">CLASS 6 · TERM 1 CURRICULUM</p>
          <h2 id="curriculum-title">Curriculum & Chapter Explorer</h2>
          <p className="muted">
            Explore authentic Tamil Nadu State Board textbooks in English across all 4 subjects.
          </p>
        </div>
        <div className="term-badge" aria-label="Academic Term">
          <GraduationCap size={16} aria-hidden="true" />
          <span>Term 1</span>
        </div>
      </div>

      {error && <div className="notice error">{error}</div>}

      {/* Subject Tabs */}
      <div className="subject-pill-tabs" role="tablist" aria-label="Class 6 Subjects">
        {subjects.map((subj) => {
          const Icon = ICON_MAP[subj.icon] || BookOpen
          const isSelected = subj.id === selectedSubjectId
          return (
            <button
              key={subj.id}
              role="tab"
              aria-selected={isSelected}
              id={`tab-subject-${subj.id}`}
              className={`subject-pill-tab ${isSelected ? 'active' : ''}`}
              onClick={() => setSelectedSubjectId(subj.id)}
              style={
                isSelected
                  ? {
                      borderColor: subj.accent_color,
                      boxShadow: `0 4px 14px ${subj.accent_color}25`,
                    }
                  : {}
              }
            >
              <span
                className="subject-tab-icon"
                style={{
                  backgroundColor: isSelected ? `${subj.accent_color}20` : '#f0eef8',
                  color: subj.accent_color,
                }}
                aria-hidden="true"
              >
                <Icon size={16} />
              </span>
              <span className="subject-tab-title">{subj.name}</span>
              <span className="subject-tab-count">{subj.chapter_count}</span>
            </button>
          )
        })}
      </div>

      {/* Chapters Listing */}
      <div className="curriculum-body">
        {loadingChapters ? (
          <div className="curriculum-loading">
            <span className="spinner" />
            <p>Loading chapters for {currentSubject?.name || 'subject'}...</p>
          </div>
        ) : chapters.length === 0 ? (
          <div className="empty compact">
            <p>No chapters available for this term yet.</p>
          </div>
        ) : (
          <div className="chapters-grid" role="list">
            {chapters.map((chap) => (
              <article
                key={chap.id}
                className="chapter-card"
                id={`chapter-card-${chap.id}`}
                role="listitem"
              >
                  <div className="chapter-header-row">
                    <div className="chapter-meta">
                      <span className="chapter-num" style={{ color: currentSubject?.accent_color }}>
                        #{chap.chapter_number}
                      </span>
                      {chap.textbook_pages && (
                        <span className="page-citation" title="Textbook Page Reference">
                          <FileText size={12} aria-hidden="true" />
                          {chap.textbook_pages}
                        </span>
                      )}
                      {chap.concept_count > 0 && (
                        <span className="concept-count-badge">
                          <Sparkles size={12} aria-hidden="true" />
                          {chap.concept_count} {chap.concept_count === 1 ? 'Concept' : 'Concepts'}
                        </span>
                      )}
                    </div>
                  </div>

                  <h3 className="chapter-title">{chap.title}</h3>
                  {chap.description && <p className="chapter-description">{chap.description}</p>}

                  <div className="chapter-actions">
                    {chap.concept_count > 0 ? (
                      <button
                        type="button"
                        className="button primary small"
                        id={`btn-open-concepts-${chap.id}`}
                        onClick={async () => {
                          // Fetch chapter detail to get first concept id
                          try {
                            const detail = await fetchChapterDetail(chap.id)
                            if (detail.concepts.length > 0) {
                              navigate(`/concept/${encodeURIComponent(detail.concepts[0].id)}`)
                            } else if (chap.lesson_id) {
                              navigate(`/lesson/${chap.lesson_id}`)
                            }
                          } catch {
                            if (chap.lesson_id) navigate(`/lesson/${chap.lesson_id}`)
                          }
                        }}
                      >
                        <PlayCircle size={14} aria-hidden="true" />
                        Start concepts <ChevronRight size={14} aria-hidden="true" />
                      </button>
                    ) : chap.lesson_id ? (
                      <button
                        type="button"
                        className="button primary small"
                        id={`btn-open-lesson-${chap.id}`}
                        onClick={() => {
                          if (onSelectLesson) onSelectLesson(chap.lesson_id!)
                          else navigate(`/lesson/${chap.lesson_id}`)
                        }}
                      >
                        Start lesson <ChevronRight size={14} aria-hidden="true" />
                      </button>
                    ) : (
                      <button
                        type="button"
                        className="button secondary small"
                        id={`btn-quiz-practice-${chap.id}`}
                        onClick={() => navigate(`/quiz?subject=${selectedSubjectId}`)}
                      >
                        Practice quiz <CircleHelp size={14} aria-hidden="true" />
                      </button>
                    )}
                  </div>
                </article>
              ))
            }
          </div>
        )}
      </div>
    </section>
  )
}
