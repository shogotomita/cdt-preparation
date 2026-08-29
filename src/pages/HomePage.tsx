import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AccuracyBar } from '../components/AccuracyBar'
import { useApp } from '../context/AppContext'
import { fetchQuestions } from '../lib/data'
import { calcSubjectAccuracy } from '../lib/progress'
import type { AccuracyStats, Question, SubjectId, YearMeta } from '../types'

function SubjectCard({
  year,
  subjectId,
  file,
  questionCount,
  label,
  passThreshold,
}: {
  year: YearMeta
  subjectId: SubjectId
  file: string
  questionCount: number
  label: string
  passThreshold: number
}) {
  const { progress } = useApp()
  const [questions, setQuestions] = useState<Question[] | null>(null)
  const [stats, setStats] = useState<AccuracyStats>({
    answered: 0,
    correct: 0,
    rate: null,
    total: questionCount,
  })

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const qs = await fetchQuestions(file)
        if (cancelled) return
        setQuestions(qs)
        setStats(calcSubjectAccuracy(progress, year.id, subjectId, qs))
      } catch {
        if (!cancelled) {
          setStats({
            answered: 0,
            correct: 0,
            rate: null,
            total: questionCount,
          })
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [file, progress, year.id, subjectId, questionCount])

  const ready = questions !== null

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-start justify-between gap-2">
        <h3 className="text-base font-bold text-gray-900">{label}</h3>
        <span className="rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
          {questionCount}問
        </span>
      </div>
      <AccuracyBar
        rate={stats.rate}
        threshold={passThreshold}
        answered={stats.answered}
        total={stats.total}
      />
      <div className="mt-4 flex flex-wrap gap-2">
        <Link
          to={`/quiz/${year.id}/${subjectId}`}
          className={`inline-flex flex-1 items-center justify-center rounded-lg bg-brand px-3 py-2.5 text-sm font-semibold text-white hover:bg-brand-hover ${
            !ready ? 'pointer-events-none opacity-50' : ''
          }`}
        >
          全問演習
        </Link>
        <Link
          to={`/quiz/${year.id}/${subjectId}?mode=weak`}
          className={`inline-flex flex-1 items-center justify-center rounded-lg border border-brand px-3 py-2.5 text-sm font-semibold text-brand hover:bg-brand-soft ${
            !ready ? 'pointer-events-none opacity-50' : ''
          }`}
        >
          苦手だけ
        </Link>
      </div>
    </div>
  )
}

export function HomePage() {
  const { index, loading, error } = useApp()

  if (loading) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center text-muted">
        読み込み中…
      </div>
    )
  }

  if (error || !index) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center text-incorrect">
        {error ?? 'データの読み込みに失敗しました'}
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 pb-16">
      <header className="mb-8">
        <p className="mb-1 text-sm font-medium text-brand">練習モード</p>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900 sm:text-3xl">
          国内旅行業務取扱管理者
          <br className="sm:hidden" />
          過去問学習
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          年度×科目ごとに正答率を記録します。各科目{' '}
          <span className="font-semibold text-gray-800">60%</span>{' '}
          以上を目指して繰り返し学習しましょう。
        </p>
      </header>

      <div className="space-y-8">
        {index.years.map((year) => (
          <section key={year.id}>
            <h2 className="mb-3 text-lg font-bold text-gray-900">
              {year.label}
            </h2>
            <div className="grid gap-3 sm:grid-cols-1">
              {year.subjects.map((ref) => {
                const meta = index.subjects.find((s) => s.id === ref.subject)
                if (!meta) return null
                return (
                  <SubjectCard
                    key={ref.subject}
                    year={year}
                    subjectId={ref.subject}
                    file={ref.file}
                    questionCount={ref.questionCount}
                    label={meta.label}
                    passThreshold={meta.passThreshold}
                  />
                )
              })}
            </div>
          </section>
        ))}
      </div>

      <p className="mt-10 text-center text-xs text-muted">
        問題データは <code className="rounded bg-gray-200 px-1">public/data</code>{' '}
        の JSON を追加して拡張できます
      </p>
    </div>
  )
}
