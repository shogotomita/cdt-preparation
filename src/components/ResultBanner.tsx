interface Props {
  isCorrect: boolean
}

export function ResultBanner({ isCorrect }: Props) {
  if (isCorrect) {
    return (
      <div className="mb-5 flex items-start gap-3 rounded-xl border border-correct-border bg-correct-bg px-4 py-3">
        <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-correct text-white text-sm">
          ✓
        </span>
        <div>
          <p className="font-semibold text-correct">正解です</p>
          <p className="text-sm text-gray-700">
            解説を確認して理解を定着させましょう。
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="mb-5 flex items-start gap-3 rounded-xl border border-incorrect-border bg-incorrect-bg px-4 py-3">
      <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-incorrect text-white text-sm font-bold">
        !
      </span>
      <div>
        <p className="font-semibold text-incorrect">不正解です</p>
        <p className="text-sm text-gray-700">
          解説を読んで、なぜ違うのかを確認しましょう。
        </p>
      </div>
    </div>
  )
}
