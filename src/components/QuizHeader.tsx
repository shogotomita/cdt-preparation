interface Props {
  current: number
  total: number
  onFinish?: () => void
}

export function QuizHeader({ current, total, onFinish }: Props) {
  const pct = total === 0 ? 0 : (current / total) * 100

  return (
    <header className="sticky top-0 z-10 border-b border-gray-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex max-w-2xl items-center gap-3 px-4 py-3">
        <span className="shrink-0 text-sm font-semibold tabular-nums text-gray-700">
          {current}/{total}
        </span>
        <div className="h-1.5 min-w-0 flex-1 overflow-hidden rounded-full bg-gray-200">
          <div
            className="h-full rounded-full bg-brand transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
        {onFinish && (
          <button
            type="button"
            onClick={onFinish}
            className="shrink-0 rounded-lg border border-brand px-3 py-1.5 text-sm font-medium text-brand hover:bg-brand-soft"
          >
            終了する
          </button>
        )}
      </div>
    </header>
  )
}
