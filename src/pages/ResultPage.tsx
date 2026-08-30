import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { AccuracyBar } from '../components/AccuracyBar'
import { useApp } from '../context/AppContext'
import { fetchQuestions, findYear, subjectFile } from '../lib/data'
import {
  calcSubjectAccuracy,
  getWrongQuestionIds,
} from '../lib/progress'
import type { Question, SubjectId } from '../types'

interface ResultState {
  correct: number
  answered: number
  total: number
  mode?: string | null
}

export function ResultPage() {
  const { yearId = '', subjectId = '' } = useParams<{
    yearId: string
    subjectId: SubjectId
  }>()
  const subject = subjectId as SubjectId
  const location = useLocation()
  const navigate = useNavigate()
  const session = (location.state ?? {}) as Partial<ResultState>
  const { index, progress, clearSubject } = useApp()

  const [questions, setQuestions] = useState<Question[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!index) return
    let cancelled = false
    ;(async () => {
      const year = findYear(index, yearId)
      const file = year ? subjectFile(year, subject) : undefined
      if (!file) {
        setLoading(false)
        return
      }
      const qs = await fetchQuestions(file)
      if (!cancelled) {
        setQuestions(qs)
        setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [index, yearId, subject])

  const subjectMeta = index?.subjects.find((s) => s.id === subject)
  const yearMeta = index ? findYear(index, yearId) : undefined
  const threshold = subjectMeta?.passThreshold ?? 60
  const stats = calcSubjectAccuracy(progress, yearId, subject, questions)
  const wrongIds = getWrongQuestionIds(progress, yearId, subject, questions)
  const sessionRate =
    session.total && session.total > 0 && (session.answered ?? 0) > 0
      ? Math.round(((session.correct ?? 0) / session.total) * 100)
      : session.answered && session.answered > 0
        ? Math.round(((session.correct ?? 0) / session.answered) * 100)
        : null
  const passed = stats.rate !== null && stats.rate >= threshold

  if (loading || !index) {
    return (
      <div className="px-4 py-16 text-center text-muted">読み込み中…</div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 pb-16">
      <p className="mb-1 text-sm text-muted">
        {yearMeta?.label} · {subjectMeta?.label}
      </p>
      <h1 className="mb-6 text-2xl font-bold text-gray-900">演習結果</h1>

      {sessionRate !== null && (
        <div className="mb-6 rounded-2xl border border-gray-200 bg-white p-5 text-center shadow-sm">
          <p className="text-sm text-muted">今回のセッション</p>
          <p className="mt-1 text-4xl font-bold tabular-nums text-brand">
            {sessionRate}%
          </p>
          <p className="mt-1 text-sm text-gray-600">
            {session.correct}/{session.total ?? session.answered} 問正解
            {session.answered != null &&
            session.total != null &&
            session.answered < session.total
              ? `（解答 ${session.answered} / ${session.total} 問）`
              : session.total
                ? `（全 ${session.total} 問）`
                : ''}
          </p>
        </div>
      )}

      <div className="mb-6 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
        <h2 className="mb-3 text-base font-bold text-gray-900">
          この科目の正答率（直近の解答）
        </h2>
        <AccuracyBar
          rate={stats.rate}
          threshold={threshold}
          answered={stats.answered}
          total={stats.total}
        />
        <p
          className={`mt-3 text-sm font-semibold ${
            stats.rate === null
              ? 'text-muted'
              : passed
                ? 'text-correct'
                : 'text-incorrect'
          }`}
        >
          {stats.rate === null
            ? 'まだ解答がありません'
            : passed
              ? `合格ライン（${threshold}%）をクリアしています`
              : `合格ライン（${threshold}%）まであと ${threshold - (stats.rate ?? 0)} ポイント`}
        </p>
      </div>

      {wrongIds.length > 0 && (
        <div className="mb-6 rounded-2xl border border-incorrect-border bg-incorrect-bg/50 p-4">
          <p className="text-sm font-semibold text-incorrect">
            直近不正解: {wrongIds.length} 問
          </p>
          <p className="mt-1 text-sm text-gray-700">
            「苦手だけ」で重点復習できます。
          </p>
        </div>
      )}

      <div className="flex flex-col gap-2">
        <Link
          to={`/quiz/${yearId}/${subject}`}
          className="rounded-lg bg-brand px-4 py-3 text-center text-sm font-semibold text-white hover:bg-brand-hover"
        >
          もう一度全問演習
        </Link>
        <Link
          to={`/quiz/${yearId}/${subject}?mode=weak`}
          className="rounded-lg border border-brand px-4 py-3 text-center text-sm font-semibold text-brand hover:bg-brand-soft"
        >
          苦手・未解答だけ復習
        </Link>
        <button
          type="button"
          onClick={() => {
            if (
              confirm(
                'この科目の学習記録をリセットしますか？（他の科目・年度には影響しません）',
              )
            ) {
              clearSubject(yearId, subject)
            }
          }}
          className="rounded-lg px-4 py-3 text-center text-sm font-medium text-muted hover:bg-gray-100"
        >
          この科目の記録をリセット
        </button>
        <button
          type="button"
          onClick={() => navigate('/')}
          className="rounded-lg px-4 py-3 text-center text-sm font-medium text-gray-700 hover:bg-gray-100"
        >
          ホームに戻る
        </button>
      </div>
    </div>
  )
}
