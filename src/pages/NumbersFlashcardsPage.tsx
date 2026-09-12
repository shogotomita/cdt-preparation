import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { FilterChip } from '../components/FilterChip'
import { fetchNumbers } from '../lib/data'
import {
  addKnownId,
  clearKnownIds,
  loadKnownIds,
} from '../lib/flashcardProgress'
import type {
  NumbersCategoryId,
  NumbersData,
  NumbersItem,
  SubjectId,
} from '../types'

const SUBJECT_LABELS: Record<SubjectId, string> = {
  hou: '旅行業法',
  yakkan: '約款',
  jitsumu: '実務',
}

function shuffle<T>(items: T[]): T[] {
  const next = [...items]
  for (let i = next.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[next[i], next[j]] = [next[j], next[i]]
  }
  return next
}

function buildDeck(
  data: NumbersData,
  categoryFilter: NumbersCategoryId | 'all',
  subjectFilter: SubjectId | 'all',
): NumbersItem[] {
  const subjectByCat = new Map(
    data.categories.map((c) => [c.id, c.subject] as const),
  )
  const items = data.items.filter((item) => {
    if (categoryFilter !== 'all' && item.category !== categoryFilter) {
      return false
    }
    if (subjectFilter !== 'all') {
      if (subjectByCat.get(item.category) !== subjectFilter) return false
    }
    return true
  })
  return shuffle(items)
}

export function NumbersFlashcardsPage() {
  const [data, setData] = useState<NumbersData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [categoryFilter, setCategoryFilter] = useState<
    NumbersCategoryId | 'all'
  >('all')
  const [subjectFilter, setSubjectFilter] = useState<SubjectId | 'all'>('all')
  const [queue, setQueue] = useState<NumbersItem[]>([])
  const [knownIds, setKnownIds] = useState(() => loadKnownIds('numbers'))
  const [knownCount, setKnownCount] = useState(0)
  const [sessionTotal, setSessionTotal] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [deckKey, setDeckKey] = useState(0)
  const knownIdsRef = useRef(knownIds)
  knownIdsRef.current = knownIds

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const nums = await fetchNumbers()
        if (cancelled) return
        setData(nums)
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : '読み込みエラー')
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!data) return
    const deck = buildDeck(data, categoryFilter, subjectFilter)
    const known = knownIdsRef.current
    setQueue(deck.filter((item) => !known.has(item.id)))
    setSessionTotal(deck.length)
    setKnownCount(deck.filter((item) => known.has(item.id)).length)
    setFlipped(false)
  }, [data, categoryFilter, subjectFilter, deckKey])

  const categoryLabels = useMemo(() => {
    const map: Record<string, string> = {}
    for (const c of data?.categories ?? []) map[c.id] = c.label
    return map
  }, [data])

  const visibleCategories = useMemo(() => {
    if (!data) return []
    if (subjectFilter === 'all') return data.categories
    return data.categories.filter((c) => c.subject === subjectFilter)
  }, [data, subjectFilter])

  const current = queue[0] ?? null
  const remaining = queue.length
  const done = sessionTotal > 0 && remaining === 0

  const markKnown = () => {
    if (!current) return
    const next = addKnownId('numbers', current.id)
    knownIdsRef.current = next
    setKnownIds(next)
    setQueue((q) => q.slice(1))
    setKnownCount((n) => n + 1)
    setFlipped(false)
  }

  const markAgain = () => {
    if (!current) return
    setQueue((q) => {
      if (q.length <= 1) return q
      const [head, ...rest] = q
      return [...rest, head]
    })
    setFlipped(false)
  }

  const restart = () => {
    if (!data) return
    const filteredIds = buildDeck(data, categoryFilter, subjectFilter).map(
      (item) => item.id,
    )
    const cleared = clearKnownIds('numbers', filteredIds)
    knownIdsRef.current = cleared
    setKnownIds(cleared)
    setDeckKey((k) => k + 1)
  }

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center text-incorrect">
        {error}
      </div>
    )
  }

  if (!data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center text-muted">
        読み込み中…
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 pb-24">
      <div className="mb-6 flex flex-wrap items-center gap-3 text-sm">
        <Link to="/" className="font-medium text-brand hover:text-brand-hover">
          ← ホーム
        </Link>
        <span className="text-muted">/</span>
        <Link
          to="/study/numbers"
          className="font-medium text-brand hover:text-brand-hover"
        >
          数字暗記ドリル
        </Link>
      </div>

      <header className="mb-6">
        <p className="mb-1 text-sm font-medium text-brand">数字・期限・金額</p>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          数字フラッシュカード
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          表面のテーマを見て数字・期限を思い出し、裏面で確認します。「もう一度」で苦手を繰り返せます（観光地理カードとは別データです）。
        </p>
      </header>

      <div className="mb-4 flex flex-col gap-3">
        <div className="flex flex-wrap gap-1.5">
          <FilterChip
            active={subjectFilter === 'all'}
            onClick={() => {
              setSubjectFilter('all')
              setCategoryFilter('all')
            }}
            label="すべて"
          />
          {(['hou', 'yakkan', 'jitsumu'] as SubjectId[]).map((s) => (
            <FilterChip
              key={s}
              active={subjectFilter === s}
              onClick={() => {
                setSubjectFilter(s)
                setCategoryFilter('all')
              }}
              label={SUBJECT_LABELS[s]}
            />
          ))}
        </div>
        <div className="flex flex-wrap gap-1.5">
          <FilterChip
            active={categoryFilter === 'all'}
            onClick={() => setCategoryFilter('all')}
            label="全カテゴリ"
          />
          {visibleCategories.map((c) => (
            <FilterChip
              key={c.id}
              active={categoryFilter === c.id}
              onClick={() => setCategoryFilter(c.id)}
              label={c.label}
            />
          ))}
        </div>
      </div>

      <div className="mb-4 flex items-center justify-between gap-2 text-sm text-muted">
        <p>
          残り <span className="font-semibold text-gray-900">{remaining}</span>
          {sessionTotal > 0 && <> / {sessionTotal}</>}
        </p>
        <p>
          覚えた <span className="font-semibold text-correct">{knownCount}</span>
        </p>
      </div>

      {sessionTotal === 0 ? (
        <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center text-sm text-muted">
          この条件に合う項目がありません。フィルタを変えてください。
        </div>
      ) : done ? (
        <div className="rounded-2xl border border-correct-border bg-correct-bg p-8 text-center">
          <p className="text-lg font-bold text-correct">一周完了</p>
          <p className="mt-2 text-sm text-muted">
            {knownCount}{' '}
            項目を覚えました。もう一周するとシャッフルし直します。
          </p>
          <button
            type="button"
            onClick={restart}
            className="mt-5 inline-flex rounded-lg bg-brand px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-hover"
          >
            もう一周
          </button>
        </div>
      ) : current ? (
        <div className="space-y-4">
          <button
            type="button"
            onClick={() => setFlipped((v) => !v)}
            className="block w-full rounded-2xl border border-gray-200 bg-white p-6 text-left shadow-sm transition hover:border-brand/40 focus:outline-none focus:ring-2 focus:ring-brand sm:p-8"
            aria-label={flipped ? '表面に戻す' : '裏面を表示'}
          >
            <p className="text-xs font-medium text-muted">
              {flipped ? '裏面 · 数字とポイント' : '表面 · タップして裏返す'}
            </p>
            {!flipped ? (
              <div className="mt-6 min-h-[140px]">
                <p className="text-xs font-semibold text-brand">
                  {categoryLabels[current.category] ?? current.category}
                </p>
                <p className="mt-2 text-2xl font-bold tracking-tight text-gray-900">
                  {current.title}
                </p>
                <p className="mt-4 text-sm text-muted">
                  関連する数字・期限は？
                </p>
              </div>
            ) : (
              <div className="mt-6 min-h-[140px]">
                <p className="text-xs font-semibold text-brand">
                  {categoryLabels[current.category] ?? current.category}
                </p>
                <p className="mt-1 text-lg font-bold text-gray-900">
                  {current.title}
                </p>
                <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-gray-800">
                  {current.bullets.map((b) => (
                    <li key={b}>{b}</li>
                  ))}
                </ul>
                {current.traps && current.traps.length > 0 && (
                  <div className="mt-4 rounded-lg bg-amber-50 px-3 py-2">
                    <p className="text-xs font-semibold text-amber-900">
                      ひっかけ
                    </p>
                    <ul className="mt-1 list-disc space-y-0.5 pl-4 text-xs leading-relaxed text-amber-950">
                      {current.traps.map((t) => (
                        <li key={t}>{t}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </button>

          <div className="flex flex-col gap-2 sm:flex-row">
            {!flipped ? (
              <button
                type="button"
                onClick={() => setFlipped(true)}
                className="flex-1 rounded-lg bg-brand px-4 py-3 text-sm font-semibold text-white hover:bg-brand-hover"
              >
                裏返す
              </button>
            ) : (
              <>
                <button
                  type="button"
                  onClick={markAgain}
                  className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm font-semibold text-gray-800 hover:bg-gray-50"
                >
                  もう一度
                </button>
                <button
                  type="button"
                  onClick={markKnown}
                  className="flex-1 rounded-lg bg-correct px-4 py-3 text-sm font-semibold text-white hover:opacity-90"
                >
                  覚えた
                </button>
              </>
            )}
          </div>
        </div>
      ) : null}
    </div>
  )
}
