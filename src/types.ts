export type SubjectId = 'hou' | 'yakkan' | 'jitsumu'

export type ChoiceKey = 'A' | 'B' | 'C' | 'D'

export interface Choice {
  key: ChoiceKey
  text: string
  explanation: string
}

export interface Question {
  id: string
  number: number
  year: string
  subject: SubjectId
  stem: string
  choices: Choice[]
  /** 正解の選択肢（複数可。「すべて選びなさい」は2つ以上） */
  correctKeys: ChoiceKey[]
  overallExplanation: string
}

export interface SubjectMeta {
  id: SubjectId
  label: string
  shortLabel: string
  passThreshold: number
}

export interface YearSubjectRef {
  subject: SubjectId
  file: string
  questionCount: number
}

export interface YearMeta {
  id: string
  label: string
  subjects: YearSubjectRef[]
}

export interface DataIndex {
  subjects: SubjectMeta[]
  years: YearMeta[]
}

export interface AttemptRecord {
  correct: boolean
  selectedKeys: ChoiceKey[]
  at: string
}

export interface QuestionProgress {
  attempts: AttemptRecord[]
}

/** year → subject → questionId → progress */
export type ProgressStore = Record<
  string,
  Record<SubjectId, Record<string, QuestionProgress>>
>

export interface AccuracyStats {
  answered: number
  correct: number
  rate: number | null
  total: number
}
