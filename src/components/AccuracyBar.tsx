export function AccuracyBar({
  rate,
  threshold = 60,
  answered,
  total,
}: {
  rate: number | null
  threshold?: number
  answered: number
  total: number
}) {
  const pct = rate ?? 0
  const passed = rate !== null && rate >= threshold
  const started = answered > 0

  return (
    <div className="space-y-1.5">
      <div className="flex items-baseline justify-between gap-2 text-sm">
        <span className="font-medium text-gray-800">
          {rate === null ? '未解答' : `正答率 ${rate}%`}
        </span>
        <span className="text-muted text-xs">
          {answered}/{total}問
          {started && (
            <span className={passed ? ' text-correct' : ' text-incorrect'}>
              {' '}
              · 合格線 {threshold}%
            </span>
          )}
        </span>
      </div>
      <div className="relative h-2 overflow-hidden rounded-full bg-gray-200">
        <div
          className={`absolute inset-y-0 left-0 rounded-full transition-all ${
            !started
              ? 'bg-gray-300'
              : passed
                ? 'bg-correct'
                : 'bg-incorrect'
          }`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
        <div
          className="absolute inset-y-0 w-px bg-gray-500/50"
          style={{ left: `${threshold}%` }}
          title={`合格ライン ${threshold}%`}
        />
      </div>
    </div>
  )
}
