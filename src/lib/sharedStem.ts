import type { Question } from '../types'

/** Leading「(…共通前提…は①と同じ。)」block, including nested parentheses. */
export function hasSharedPlaceholder(stem: string): boolean {
  return /^\([\s\S]*共通前提/.test(stem)
}

/** Find the first sibling that owns the shared stem (…-1 / …①). */
export function findSharedSource(
  question: Question,
  allQuestions: Question[],
): Question | null {
  const m = question.id.match(/^(.*-)(\d+)$/)
  if (!m) return null
  const n = Number(m[2])
  if (!Number.isFinite(n) || n <= 1) return null
  const sourceId = `${m[1]}1`
  if (sourceId === question.id) return null
  return allQuestions.find((q) => q.id === sourceId) ?? null
}

/** Drop the trailing ①/(1) sub-question (and anything after it) from a source stem. */
export function stripTerminalSubquestion(stem: string): string {
  // Match ①… or (1)… question markers, but not notes like (注1)
  const cut = stem.search(/\n(?:[①-⑩]|\(\d+\))/u)
  if (cut >= 0) return stem.slice(0, cut).trimEnd()
  return stem.trimEnd()
}

/** Remove the leading「共通前提は①と同じ」placeholder. */
export function stripSharedPlaceholder(stem: string): string {
  if (!hasSharedPlaceholder(stem) || stem[0] !== '(') return stem
  let depth = 0
  for (let i = 0; i < stem.length; i += 1) {
    const ch = stem[i]
    if (ch === '(') depth += 1
    else if (ch === ')') {
      depth -= 1
      if (depth === 0) {
        return stem.slice(i + 1).replace(/^\s+/, '')
      }
    }
  }
  return stem
}

/**
 * When a later sub-question only references shared premises, expand it with
 * the sibling's shared body so one-question-at-a-time UI stays answerable.
 */
export function resolveSharedStem(
  question: Question,
  allQuestions: Question[],
): string {
  if (!hasSharedPlaceholder(question.stem)) {
    return question.stem
  }
  const source = findSharedSource(question, allQuestions)
  if (!source) return question.stem

  const shared = stripTerminalSubquestion(source.stem)
  let rest = stripSharedPlaceholder(question.stem)

  // Avoid duplicate <図> when both shared and rest include the marker.
  if (shared.includes('<図>') && rest.startsWith('<図>')) {
    rest = rest.replace(/^<図>\s*/, '').trimStart()
  }

  if (!shared) return question.stem
  if (!rest) return shared
  return `${shared}\n\n${rest}`
}
