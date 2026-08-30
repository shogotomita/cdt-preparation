import type {
  AccuracyStats,
  ChoiceKey,
  ProgressStore,
  Question,
  QuestionProgress,
  SubjectId,
} from '../types'

const STORAGE_KEY = 'cdt-progress-v1'

function emptyStore(): ProgressStore {
  return {}
}

export function loadProgress(): ProgressStore {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return emptyStore()
    return JSON.parse(raw) as ProgressStore
  } catch {
    return emptyStore()
  }
}

export function saveProgress(store: ProgressStore): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(store))
}

export function recordAttempt(
  store: ProgressStore,
  year: string,
  subject: SubjectId,
  questionId: string,
  selectedKeys: ChoiceKey[],
  correct: boolean,
): ProgressStore {
  const next: ProgressStore = structuredClone(store)
  if (!next[year]) next[year] = {} as ProgressStore[string]
  if (!next[year][subject]) next[year][subject] = {}
  const qp: QuestionProgress = next[year][subject][questionId] ?? {
    attempts: [],
  }
  qp.attempts.push({
    correct,
    selectedKeys,
    at: new Date().toISOString(),
  })
  next[year][subject][questionId] = qp
  saveProgress(next)
  return next
}

export function latestAttempt(qp: QuestionProgress | undefined) {
  if (!qp?.attempts.length) return null
  return qp.attempts[qp.attempts.length - 1]
}

/**
 * 直近1回の解答に基づく年度×科目の正答率。
 * 分母は科目の全問数（未解答は不正解扱い）。解答0件のとき rate は null。
 */
export function calcSubjectAccuracy(
  store: ProgressStore,
  year: string,
  subject: SubjectId,
  questions: Question[],
): AccuracyStats {
  const subjectProg = store[year]?.[subject] ?? {}
  let answered = 0
  let correct = 0
  const total = questions.length

  for (const q of questions) {
    const latest = latestAttempt(subjectProg[q.id])
    if (!latest) continue
    answered += 1
    if (latest.correct) correct += 1
  }

  return {
    answered,
    correct,
    rate: answered === 0 || total === 0 ? null : Math.round((correct / total) * 100),
    total,
  }
}

/** 指定問題セットについて、直近解答からの正解数・解答数を集計 */
export function calcQueueSessionStats(
  store: ProgressStore,
  year: string,
  subject: SubjectId,
  questions: Question[],
): { correct: number; answered: number; total: number } {
  const subjectProg = store[year]?.[subject] ?? {}
  let answered = 0
  let correct = 0
  for (const q of questions) {
    const latest = latestAttempt(subjectProg[q.id])
    if (!latest) continue
    answered += 1
    if (latest.correct) correct += 1
  }
  return { correct, answered, total: questions.length }
}

/** 累計（全試行）の正答率 */
export function calcSubjectCumulativeAccuracy(
  store: ProgressStore,
  year: string,
  subject: SubjectId,
): AccuracyStats {
  const subjectProg = store[year]?.[subject] ?? {}
  let answered = 0
  let correct = 0

  for (const qp of Object.values(subjectProg) as QuestionProgress[]) {
    for (const a of qp.attempts) {
      answered += 1
      if (a.correct) correct += 1
    }
  }

  return {
    answered,
    correct,
    rate: answered === 0 ? null : Math.round((correct / answered) * 100),
    total: answered,
  }
}

export function getWrongQuestionIds(
  store: ProgressStore,
  year: string,
  subject: SubjectId,
  questions: Question[],
): string[] {
  const subjectProg = store[year]?.[subject] ?? {}
  return questions
    .filter((q) => {
      const latest = latestAttempt(subjectProg[q.id])
      return latest && !latest.correct
    })
    .map((q) => q.id)
}

export function getUnansweredOrWrongIds(
  store: ProgressStore,
  year: string,
  subject: SubjectId,
  questions: Question[],
): string[] {
  const subjectProg = store[year]?.[subject] ?? {}
  return questions
    .filter((q) => {
      const latest = latestAttempt(subjectProg[q.id])
      return !latest || !latest.correct
    })
    .map((q) => q.id)
}

export function clearSubjectProgress(
  store: ProgressStore,
  year: string,
  subject: SubjectId,
): ProgressStore {
  const next: ProgressStore = structuredClone(store)
  if (next[year]) {
    next[year][subject] = {}
  }
  saveProgress(next)
  return next
}
