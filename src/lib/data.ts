import type { DataIndex, Question, SubjectId, YearMeta } from '../types'

/** public 配下のパスを Vite `base` 付き URL にする（GitHub Pages のサブパス対応） */
export function publicUrl(path: string): string {
  if (/^https?:\/\//.test(path)) return path
  const base = import.meta.env.BASE_URL
  const normalized = base.endsWith('/') ? base : `${base}/`
  return `${normalized}${path.replace(/^\/+/, '')}`
}

function dataUrl(path: string): string {
  return publicUrl(`data/${path}`)
}

export async function fetchIndex(): Promise<DataIndex> {
  const res = await fetch(dataUrl('index.json'))
  if (!res.ok) throw new Error('データ一覧の読み込みに失敗しました')
  return res.json() as Promise<DataIndex>
}

export async function fetchQuestions(file: string): Promise<Question[]> {
  const res = await fetch(dataUrl(file))
  if (!res.ok) throw new Error(`問題データの読み込みに失敗: ${file}`)
  const json = (await res.json()) as { questions: Question[] }
  return json.questions
}

export function findYear(index: DataIndex, yearId: string): YearMeta | undefined {
  return index.years.find((y) => y.id === yearId)
}

export function subjectFile(
  year: YearMeta,
  subject: SubjectId,
): string | undefined {
  return year.subjects.find((s) => s.subject === subject)?.file
}
