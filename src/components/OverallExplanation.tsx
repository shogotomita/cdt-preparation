import type { Question } from '../types'

export function OverallExplanation({ question }: { question: Question }) {
  return (
    <section className="rounded-xl border border-gray-200 bg-white p-4 sm:p-5">
      <h2 className="mb-3 text-base font-bold text-gray-900">全体の解説</h2>
      <p className="text-sm leading-relaxed text-gray-700 whitespace-pre-wrap">
        {question.overallExplanation}
      </p>
    </section>
  )
}
