import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { ChoiceList } from '../components/ChoiceList'
import { OverallExplanation } from '../components/OverallExplanation'
import { QuizHeader } from '../components/QuizHeader'
import { ResultBanner } from '../components/ResultBanner'
import { useApp } from '../context/AppContext'
import { fetchQuestions, findYear, subjectFile } from '../lib/data'
import { getUnansweredOrWrongIds } from '../lib/progress'
import { isAnswerCorrect, isMultiSelect } from '../lib/quiz'
import type { ChoiceKey, Question, SubjectId } from '../types'

export function QuizPage() {
  const { yearId = '', subjectId = '' } = useParams<{
    yearId: string
    subjectId: SubjectId
  }>()
  const [searchParams] = useSearchParams()
  const mode = searchParams.get('mode') // 'weak' | null
  const navigate = useNavigate()
  const { index, progress, record } = useApp()

  const [allQuestions, setAllQuestions] = useState<Question[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [indexQ, setIndexQ] = useState(0)
  const [selected, setSelected] = useState<ChoiceKey[]>([])
  const [submitted, setSubmitted] = useState(false)
  const [sessionCorrect, setSessionCorrect] = useState(0)
  const [sessionAnswered, setSessionAnswered] = useState(0)

  const subject = subjectId as SubjectId

  useEffect(() => {
    if (!index) return
    let cancelled = false
    ;(async () => {
      try {
        const year = findYear(index, yearId)
        if (!year) throw new Error('年度が見つかりません')
        const file = subjectFile(year, subject)
        if (!file) throw new Error('科目データが見つかりません')
        const qs = await fetchQuestions(file)
        if (cancelled) return

        let queue = qs
        if (mode === 'weak') {
          const weakIds = new Set(
            getUnansweredOrWrongIds(progress, yearId, subject, qs),
          )
          queue = qs.filter((q) => weakIds.has(q.id))
          if (queue.length === 0) {
            queue = qs
          }
        }

        setAllQuestions(queue)
        setLoading(false)
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
    // progress intentionally omitted: queue is fixed at session start
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index, yearId, subject, mode])

  const question = allQuestions[indexQ]
  const subjectMeta = index?.subjects.find((s) => s.id === subject)
  const yearMeta = index ? findYear(index, yearId) : undefined
  const multi = question ? isMultiSelect(question) : false

  const isCorrect = useMemo(
    () =>
      submitted && question ? isAnswerCorrect(question, selected) : false,
    [submitted, selected, question],
  )

  function resetQuestionState() {
    setSelected([])
    setSubmitted(false)
  }

  function handleToggle(key: ChoiceKey) {
    if (submitted) return
    if (multi) {
      setSelected((prev) =>
        prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key],
      )
      return
    }
    setSelected([key])
  }

  function handleCheck() {
    if (!question || selected.length === 0) return
    const ok = isAnswerCorrect(question, selected)
    record(yearId, subject, question.id, selected, ok)
    setSubmitted(true)
    setSessionAnswered((n) => n + 1)
    if (ok) setSessionCorrect((n) => n + 1)
  }

  function handleNext() {
    if (indexQ >= allQuestions.length - 1) {
      navigate(`/result/${yearId}/${subject}`, {
        state: {
          correct: sessionCorrect,
          answered: sessionAnswered,
          total: allQuestions.length,
          mode,
        },
      })
      return
    }
    setIndexQ((i) => i + 1)
    resetQuestionState()
  }

  function handleFinish() {
    navigate(`/result/${yearId}/${subject}`, {
      state: {
        correct: sessionCorrect,
        answered: sessionAnswered,
        total: allQuestions.length,
        mode,
      },
    })
  }

  if (loading) {
    return (
      <div className="px-4 py-16 text-center text-muted">読み込み中…</div>
    )
  }

  if (error || !question) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <p className="mb-4 text-incorrect">{error ?? '問題がありません'}</p>
        <Link to="/" className="text-brand underline">
          ホームに戻る
        </Link>
      </div>
    )
  }

  return (
    <div className="flex min-h-full flex-col pb-24">
      <QuizHeader
        current={indexQ + 1}
        total={allQuestions.length}
        onFinish={handleFinish}
      />

      <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-6">
        <p className="mb-1 text-xs font-medium text-muted">
          {yearMeta?.label} · {subjectMeta?.label}
          {mode === 'weak' ? ' · 苦手優先' : ''}
        </p>
        <h1 className="mb-4 flex items-start gap-2 text-base font-bold text-gray-900">
          <span aria-hidden className="mt-0.5 text-brand">
            ▸
          </span>
          <span>問題 {question.number}</span>
        </h1>

        {submitted && <ResultBanner isCorrect={isCorrect} />}

        <p className="mb-6 text-[15px] leading-relaxed whitespace-pre-wrap text-gray-900">
          {question.stem}
        </p>
        {multi && !submitted && (
          <p className="-mt-4 mb-6 text-xs text-muted">
            ※ 当てはまるものをすべて選択
          </p>
        )}

        <ChoiceList
          question={question}
          selected={selected}
          submitted={submitted}
          onToggle={handleToggle}
        />

        {submitted && (
          <div className="mt-6">
            <OverallExplanation question={question} />
          </div>
        )}
      </main>

      <footer className="fixed inset-x-0 bottom-0 border-t border-gray-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-2xl items-center justify-between gap-3 px-4 py-3">
          <button
            type="button"
            onClick={() => {
              if (indexQ === 0) {
                navigate('/')
                return
              }
              setIndexQ((i) => i - 1)
              resetQuestionState()
            }}
            className="text-sm font-medium text-gray-600 hover:text-gray-900"
          >
            {indexQ === 0 ? 'ホーム' : '戻る'}
          </button>

          {!submitted ? (
            <button
              type="button"
              disabled={selected.length === 0}
              onClick={handleCheck}
              className="rounded-lg bg-brand px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-hover disabled:cursor-not-allowed disabled:opacity-40"
            >
              答えを確認 →
            </button>
          ) : (
            <button
              type="button"
              onClick={handleNext}
              className="rounded-lg bg-brand px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-hover"
            >
              {indexQ >= allQuestions.length - 1
                ? '結果を見る →'
                : '次の問題 →'}
            </button>
          )}
        </div>
      </footer>
    </div>
  )
}
