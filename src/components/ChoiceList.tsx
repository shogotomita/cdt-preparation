import type { Choice, ChoiceKey, Question } from '../types'

interface Props {
  question: Question
  selected: ChoiceKey | null
  submitted: boolean
  onSelect: (key: ChoiceKey) => void
}

function choiceState(
  choice: Choice,
  selected: ChoiceKey | null,
  submitted: boolean,
  correctKey: ChoiceKey,
) {
  if (!submitted) {
    if (selected === choice.key) {
      return {
        box: 'border-brand bg-brand-soft ring-1 ring-brand',
        icon: 'selected' as const,
      }
    }
    return {
      box: 'border-gray-300 bg-white hover:border-gray-400',
      icon: 'idle' as const,
    }
  }

  const isCorrect = choice.key === correctKey
  const isSelected = choice.key === selected

  if (isCorrect) {
    return {
      box: 'border-correct-border bg-correct-bg',
      icon: 'correct' as const,
    }
  }
  if (isSelected && !isCorrect) {
    return {
      box: 'border-incorrect-border bg-incorrect-bg',
      icon: 'incorrect' as const,
    }
  }
  return {
    box: 'border-gray-200 bg-white opacity-90',
    icon: 'idle' as const,
  }
}

function StatusIcon({
  icon,
}: {
  icon: 'idle' | 'selected' | 'correct' | 'incorrect'
}) {
  if (icon === 'correct') {
    return (
      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-correct text-white">
        <svg viewBox="0 0 16 16" className="h-3 w-3" fill="none" aria-hidden>
          <path
            d="M3.5 8.5 6.5 11.5 12.5 4.5"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
    )
  }
  if (icon === 'incorrect') {
    return (
      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-incorrect text-white">
        <svg viewBox="0 0 16 16" className="h-3 w-3" fill="none" aria-hidden>
          <path
            d="M4 4l8 8M12 4l-8 8"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
      </span>
    )
  }
  if (icon === 'selected') {
    return (
      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-[5px] border-brand bg-white" />
    )
  }
  return (
    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 border-gray-300 bg-white" />
  )
}

export function ChoiceList({
  question,
  selected,
  submitted,
  onSelect,
}: Props) {
  return (
    <ul className="space-y-3">
      {question.choices.map((choice) => {
        const state = choiceState(
          choice,
          selected,
          submitted,
          question.correctKey,
        )
        return (
          <li key={choice.key}>
            <button
              type="button"
              disabled={submitted}
              onClick={() => onSelect(choice.key)}
              className={`w-full rounded-xl border px-4 py-3.5 text-left transition ${state.box} ${
                submitted ? 'cursor-default' : 'cursor-pointer'
              }`}
            >
              {submitted && choice.key === question.correctKey && (
                <p className="mb-1 text-xs font-semibold text-correct">
                  正解
                </p>
              )}
              {submitted &&
                choice.key === selected &&
                choice.key !== question.correctKey && (
                  <p className="mb-1 text-xs font-semibold text-incorrect">
                    あなたの回答（不正解）
                  </p>
                )}
              <div className="flex items-start gap-3">
                <StatusIcon icon={state.icon} />
                <div className="min-w-0 flex-1">
                  <p className="text-[15px] leading-relaxed text-gray-900">
                    <span className="font-semibold">{choice.key}. </span>
                    {choice.text}
                  </p>
                  {submitted && (
                    <div className="mt-3 border-t border-black/5 pt-3">
                      <p className="mb-1 text-xs font-semibold text-gray-500">
                        解説
                      </p>
                      <p className="text-sm leading-relaxed text-gray-700 whitespace-pre-wrap">
                        {choice.explanation}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
