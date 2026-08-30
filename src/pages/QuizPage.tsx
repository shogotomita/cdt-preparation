import { Fragment, useEffect, useMemo, useState, type ReactNode } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { ChoiceList } from '../components/ChoiceList'
import { OverallExplanation } from '../components/OverallExplanation'
import { QuizHeader } from '../components/QuizHeader'
import { QuizToc } from '../components/QuizToc'
import { ResultBanner } from '../components/ResultBanner'
import { useApp } from '../context/AppContext'
import { fetchQuestions, findYear, subjectFile } from '../lib/data'
import {
  calcQueueSessionStats,
  getUnansweredOrWrongIds,
  latestAttempt,
  loadProgress,
} from '../lib/progress'
import { isAnswerCorrect, isMultiSelect } from '../lib/quiz'
import type { ChoiceKey, Question, SubjectId } from '../types'

const IMAGE_MARKER = '<図>'

/** stem 内の <u>...</u> を下線付きで描画（他タグはテキストのまま） */
function renderRichText(text: string) {
  const nodes: ReactNode[] = []
  const re = /<u>(.*?)<\/u>/gs
  let last = 0
  let match: RegExpExecArray | null
  let key = 0
  while ((match = re.exec(text)) !== null) {
    if (match.index > last) {
      nodes.push(text.slice(last, match.index))
    }
    nodes.push(
      <u key={key++} className="underline decoration-2 underline-offset-2">
        {match[1]}
      </u>,
    )
    last = match.index + match[0].length
  }
  if (last < text.length) {
    nodes.push(text.slice(last))
  }
  return nodes
}

function QuestionStem({ question }: { question: Question }) {
  const images = question.images ?? []
  const parts = question.stem.split(IMAGE_MARKER)
  const hasMarker = parts.length > 1

  const textClass =
    'text-[15px] leading-relaxed whitespace-pre-wrap text-gray-900'

  function renderImages() {
    if (images.length === 0) return null
    return (
      <div className="flex flex-col gap-3">
        {images.map((src, i) => (
          <img
            key={src}
            src={src}
            alt={`問題${question.number}の図${i + 1}`}
            className="h-auto w-full max-w-full rounded-md border border-gray-200 bg-white"
          />
        ))}
      </div>
    )
  }

  function renderText(part: string) {
    if (part === '') return null
    return <p className={textClass}>{renderRichText(part)}</p>
  }

  if (!hasMarker) {
    return (
      <div className="mb-6 flex flex-col gap-4">
        {renderText(question.stem)}
        {renderImages()}
      </div>
    )
  }

  return (
    <div className="mb-6 flex flex-col gap-4">
      {parts.map((part, i) => (
        <Fragment key={i}>
          {renderText(part)}
          {i < parts.length - 1 && renderImages()}
        </Fragment>
      ))}
    </div>
  )
}

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

  // 問題切替時: 保存済みの直近解答があれば復元（結果画面で手動リセットするまで保持）
  useEffect(() => {
    if (!question) return
    const latest = latestAttempt(
      progress[yearId]?.[subject]?.[question.id],
    )
    if (latest) {
      setSelected([...latest.selectedKeys])
      setSubmitted(true)
    } else {
      setSelected([])
      setSubmitted(false)
    }
    // progress は復元のソース。record 直後も同じ選択で上書きされるだけ
  }, [question, yearId, subject, progress])

  const isCorrect = useMemo(
    () =>
      submitted && question ? isAnswerCorrect(question, selected) : false,
    [submitted, selected, question],
  )

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
    if (!question || selected.length === 0 || submitted) return
    const ok = isAnswerCorrect(question, selected)
    record(yearId, subject, question.id, selected, ok)
    setSubmitted(true)
  }

  function navigateToResult() {
    // recordAttempt は localStorage に同期書き込み済みなので、最新状態から集計
    const stats = calcQueueSessionStats(
      loadProgress(),
      yearId,
      subject,
      allQuestions,
    )
    navigate(`/result/${yearId}/${subject}`, {
      state: {
        ...stats,
        mode,
      },
    })
  }

  function handleNext() {
    if (indexQ >= allQuestions.length - 1) {
      navigateToResult()
      return
    }
    setIndexQ((i) => i + 1)
    window.scrollTo(0, 0)
  }

  function handleJump(i: number) {
    if (i === indexQ) return
    setIndexQ(i)
    window.scrollTo(0, 0)
  }

  function handleFinish() {
    navigateToResult()
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

      <QuizToc
        questions={allQuestions}
        currentIndex={indexQ}
        yearId={yearId}
        subject={subject}
        progress={progress}
        onSelect={handleJump}
      />

      <div className="flex min-h-0 flex-1 flex-col lg:pl-44">
        <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-6">
          <p className="mb-1 text-xs font-medium text-muted">
            {yearMeta?.label} · {subjectMeta?.label}
            {mode === 'weak' ? ' · 苦手優先' : ''}
          </p>
          <h1 className="mb-4 flex items-start gap-2 text-base font-bold text-gray-900">
            <span aria-hidden className="mt-0.5 text-brand">
              ▸
            </span>
            <span>問題 {question.displayNumber ?? question.number}</span>
          </h1>

          {submitted && <ResultBanner isCorrect={isCorrect} />}

          <QuestionStem question={question} />
          {multi && !submitted && (
            <p className="mb-6 -mt-2 text-xs text-muted">
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
      </div>

      <footer className="fixed inset-x-0 bottom-0 border-t border-gray-200 bg-white/95 backdrop-blur lg:left-44">
        <div className="mx-auto flex max-w-2xl items-center justify-between gap-3 px-4 py-3">
          <button
            type="button"
            onClick={() => {
              if (indexQ === 0) {
                navigate('/')
                return
              }
              handleJump(indexQ - 1)
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
