import type { ChoiceKey, Question } from '../types'

export function isMultiSelect(question: Question): boolean {
  if (question.correctKeys.length > 1) return true
  if (question.correctKeys.length === 0 && question.stem.includes('すべて')) {
    return true
  }
  return false
}

export function sameKeySet(a: ChoiceKey[], b: ChoiceKey[]): boolean {
  if (a.length !== b.length) return false
  const sa = [...a].sort().join(',')
  const sb = [...b].sort().join(',')
  return sa === sb
}

export function isAnswerCorrect(
  question: Question,
  selected: ChoiceKey[],
): boolean {
  if (question.correctKeys.length === 0) return false
  return sameKeySet(selected, question.correctKeys)
}
