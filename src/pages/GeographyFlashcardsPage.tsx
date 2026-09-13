import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { FilterChip } from '../components/FilterChip'
import { fetchGeography } from '../lib/data'
import {
  addKnownId,
  clearAllKnownIds,
  clearKnownIds,
  loadKnownIds,
} from '../lib/flashcardProgress'
import type {
  GeographyData,
  GeographyFact,
  GeographyFactType,
} from '../types'

const REGIONS = [
  '北海道',
  '東北',
  '関東',
  '中部',
  '近畿',
  '中国',
  '四国',
  '九州・沖縄',
] as const

type CardItem = {
  id: string
  prefId: string
  prefName: string
  region: string
  fact: GeographyFact
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
  data: GeographyData,
  regionFilter: string,
  typeFilter: GeographyFactType | 'all',
): CardItem[] {
  const items: CardItem[] = []
  for (const pref of data.prefectures) {
    if (regionFilter !== 'all' && pref.region !== regionFilter) continue
    for (const fact of pref.facts) {
      if (typeFilter !== 'all' && fact.type !== typeFilter) continue
      items.push({
        id: `${pref.id}:${fact.type}:${fact.label}`,
        prefId: pref.id,
        prefName: pref.name,
        region: pref.region,
        fact,
      })
    }
  }
  return shuffle(items)
}

export function GeographyFlashcardsPage() {
  const [data, setData] = useState<GeographyData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [typeFilter, setTypeFilter] = useState<GeographyFactType | 'all'>('all')
  const [regionFilter, setRegionFilter] = useState<string>('all')
  const [queue, setQueue] = useState<CardItem[]>([])
  const [knownIds, setKnownIds] = useState(() => loadKnownIds('geography'))
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
        const geo = await fetchGeography()
        if (cancelled) return
        setData(geo)
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
    const deck = buildDeck(data, regionFilter, typeFilter)
    const known = knownIdsRef.current
    setQueue(deck.filter((item) => !known.has(item.id)))
    setSessionTotal(deck.length)
    setKnownCount(deck.filter((item) => known.has(item.id)).length)
    setFlipped(false)
  }, [data, regionFilter, typeFilter, deckKey])

  const typeLabels = useMemo(() => {
    const map: Record<string, string> = {}
    for (const t of data?.types ?? []) map[t.id] = t.label
    return map
  }, [data])

  const current = queue[0] ?? null
  const remaining = queue.length
  const done = sessionTotal > 0 && remaining === 0

  const markKnown = () => {
    if (!current) return
    const next = addKnownId('geography', current.id)
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
    const filteredIds = buildDeck(data, regionFilter, typeFilter).map(
      (item) => item.id,
    )
    const cleared = clearKnownIds('geography', filteredIds)
    knownIdsRef.current = cleared
    setKnownIds(cleared)
    setDeckKey((k) => k + 1)
  }

  const resetAllKnown = () => {
    const cleared = clearAllKnownIds('geography')
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
          to="/study/geography"
          className="font-medium text-brand hover:text-brand-hover"
        >
          観光地理ドリル
        </Link>
      </div>

      <header className="mb-6">
        <p className="mb-1 text-sm font-medium text-brand">国内旅行実務</p>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          フラッシュカード
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          表面の名所・特産を見て都道府県と特徴を思い出し、裏面で確認します。「もう一度」で苦手を繰り返せます。
        </p>
      </header>

      <div className="mb-4 flex flex-col gap-3">
        <div className="flex flex-wrap gap-1.5">
          <FilterChip
            active={typeFilter === 'all'}
            onClick={() => setTypeFilter('all')}
            label="すべて"
          />
          {data.types.map((t) => (
            <FilterChip
              key={t.id}
              active={typeFilter === t.id}
              onClick={() => setTypeFilter(t.id)}
              label={t.label}
            />
          ))}
        </div>
        <div className="flex flex-wrap gap-1.5">
          <FilterChip
            active={regionFilter === 'all'}
            onClick={() => setRegionFilter('all')}
            label="全国"
          />
          {REGIONS.map((r) => (
            <FilterChip
              key={r}
              active={regionFilter === r}
              onClick={() => setRegionFilter(r)}
              label={r}
            />
          ))}
        </div>
      </div>

      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 text-sm text-muted">
        <p>
          残り <span className="font-semibold text-gray-900">{remaining}</span>
          {sessionTotal > 0 && (
            <>
              {' '}
              / {sessionTotal}
            </>
          )}
        </p>
        <div className="flex items-center gap-3">
          <p>
            覚えた{' '}
            <span className="font-semibold text-correct">{knownCount}</span>
          </p>
          {knownIds.size > 0 && (
            <button
              type="button"
              onClick={resetAllKnown}
              className="text-xs font-medium text-muted underline-offset-2 hover:text-gray-800 hover:underline"
            >
              覚えたをリセット
            </button>
          )}
        </div>
      </div>

      {sessionTotal === 0 ? (
        <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center text-sm text-muted">
          この条件に合う項目がありません。フィルタを変えてください。
        </div>
      ) : done ? (
        <div className="rounded-2xl border border-correct-border bg-correct-bg p-8 text-center">
          <p className="text-lg font-bold text-correct">一周完了</p>
          <p className="mt-2 text-sm text-muted">
            {knownCount} 項目を覚えました。もう一周するとシャッフルし直します。
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
              {flipped ? '裏面 · 所在地と特徴' : '表面 · タップして裏返す'}
            </p>
            {!flipped ? (
              <div className="mt-6 min-h-[140px]">
                <p className="text-xs font-semibold text-brand">
                  {typeLabels[current.fact.type] ?? current.fact.type}
                </p>
                <p className="mt-2 text-2xl font-bold tracking-tight text-gray-900">
                  {current.fact.label}
                </p>
                <p className="mt-4 text-sm text-muted">どこの都道府県？</p>
              </div>
            ) : (
              <div className="mt-6 min-h-[140px]">
                <p className="text-xs font-medium text-muted">{current.region}</p>
                <p className="mt-1 text-2xl font-bold text-brand">
                  {current.prefName}
                </p>
                <p className="mt-3 text-base font-semibold text-gray-900">
                  {current.fact.label}
                </p>
                {current.fact.hooks.length > 0 && (
                  <p className="mt-3 text-sm leading-relaxed text-muted">
                    {current.fact.hooks.join(' · ')}
                  </p>
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
