import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { fetchIndex } from '../lib/data'
import {
  clearSubjectProgress,
  loadProgress,
  recordAttempt,
} from '../lib/progress'
import type {
  ChoiceKey,
  DataIndex,
  ProgressStore,
  SubjectId,
} from '../types'

interface AppState {
  index: DataIndex | null
  loading: boolean
  error: string | null
  progress: ProgressStore
  record: (
    year: string,
    subject: SubjectId,
    questionId: string,
    selectedKey: ChoiceKey,
    correct: boolean,
  ) => void
  clearSubject: (year: string, subject: SubjectId) => void
  refreshProgress: () => void
}

const AppContext = createContext<AppState | null>(null)

export function AppProvider({ children }: { children: ReactNode }) {
  const [index, setIndex] = useState<DataIndex | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState<ProgressStore>(() => loadProgress())

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const data = await fetchIndex()
        if (!cancelled) {
          setIndex(data)
          setLoading(false)
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : '読み込みエラー')
          setLoading(false)
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const record = useCallback(
    (
      year: string,
      subject: SubjectId,
      questionId: string,
      selectedKey: ChoiceKey,
      correct: boolean,
    ) => {
      setProgress((prev) =>
        recordAttempt(prev, year, subject, questionId, selectedKey, correct),
      )
    },
    [],
  )

  const clearSubject = useCallback((year: string, subject: SubjectId) => {
    setProgress((prev) => clearSubjectProgress(prev, year, subject))
  }, [])

  const refreshProgress = useCallback(() => {
    setProgress(loadProgress())
  }, [])

  const value = useMemo(
    () => ({
      index,
      loading,
      error,
      progress,
      record,
      clearSubject,
      refreshProgress,
    }),
    [index, loading, error, progress, record, clearSubject, refreshProgress],
  )

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp(): AppState {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used within AppProvider')
  return ctx
}
