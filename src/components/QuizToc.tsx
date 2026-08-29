import type { ProgressStore, Question, SubjectId } from '../types'

type AttemptStatus = 'unanswered' | 'correct' | 'incorrect'

function latestStatus(
  progress: ProgressStore,
  year: string,
  subject: SubjectId,
  questionId: string,
): AttemptStatus {
  const attempts = progress[year]?.[subject]?.[questionId]?.attempts
  if (!attempts?.length) return 'unanswered'
  return attempts[attempts.length - 1].correct ? 'correct' : 'incorrect'
}

interface Props {
  questions: Question[]
  currentIndex: number
  yearId: string
  subject: SubjectId
  progress: ProgressStore
  onSelect: (index: number) => void
}

export function QuizToc({
  questions,
  currentIndex,
  yearId,
  subject,
  progress,
  onSelect,
}: Props) {
  return (
    <>
      {/* Mobile: horizontal strip under header */}
      <nav
        aria-label="問題一覧"
        className="sticky top-[53px] z-[9] border-b border-gray-200 bg-white/95 backdrop-blur lg:hidden"
      >
        <ul className="flex gap-1.5 overflow-x-auto px-4 py-2">
          {questions.map((q, i) => (
            <li key={q.id} className="shrink-0">
              <TocButton
                label={`問${q.displayNumber ?? q.number}`}
                status={latestStatus(progress, yearId, subject, q.id)}
                active={i === currentIndex}
                onClick={() => onSelect(i)}
                compact
              />
            </li>
          ))}
        </ul>
      </nav>

      {/* Desktop: left sidebar */}
      <aside
        aria-label="問題目次"
        className="fixed top-[53px] bottom-[61px] left-0 z-20 hidden w-44 overflow-y-auto border-r border-gray-200 bg-white px-3 py-4 lg:block"
      >
        <p className="mb-3 px-1 text-xs font-semibold tracking-wide text-muted">
          目次
        </p>
        <ul className="flex flex-col gap-1">
          {questions.map((q, i) => (
            <li key={q.id}>
              <TocButton
                label={`問 ${q.displayNumber ?? q.number}`}
                status={latestStatus(progress, yearId, subject, q.id)}
                active={i === currentIndex}
                onClick={() => onSelect(i)}
              />
            </li>
          ))}
        </ul>
      </aside>
    </>
  )
}

function TocButton({
  label,
  status,
  active,
  onClick,
  compact = false,
}: {
  label: string
  status: AttemptStatus
  active: boolean
  onClick: () => void
  compact?: boolean
}) {
  const statusDot =
    status === 'correct'
      ? 'bg-correct'
      : status === 'incorrect'
        ? 'bg-incorrect'
        : 'bg-gray-300'

  const base = compact
    ? 'inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium tabular-nums'
    : 'flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm font-medium tabular-nums'

  const tone = active
    ? 'bg-brand-soft text-brand'
    : 'text-gray-700 hover:bg-gray-100'

  return (
    <button type="button" onClick={onClick} className={`${base} ${tone}`}>
      <span
        aria-hidden
        className={`h-1.5 w-1.5 shrink-0 rounded-full ${statusDot}`}
      />
      <span>{label}</span>
      {active && <span className="sr-only">（表示中）</span>}
    </button>
  )
}
