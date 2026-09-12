import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { FilterChip } from '../components/FilterChip'
import { fetchGeography } from '../lib/data'
import type {
  GeographyData,
  GeographyFact,
  GeographyFactType,
  GeographyPrefecture,
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

function factMatches(
  fact: GeographyFact,
  query: string,
  typeFilter: GeographyFactType | 'all',
): boolean {
  if (typeFilter !== 'all' && fact.type !== typeFilter) return false
  if (!query) return true
  const q = query.toLowerCase()
  return (
    fact.label.toLowerCase().includes(q) ||
    fact.hooks.some((h) => h.toLowerCase().includes(q))
  )
}

function prefMatches(
  pref: GeographyPrefecture,
  query: string,
  typeFilter: GeographyFactType | 'all',
): boolean {
  if (!query) {
    return pref.facts.some((f) => factMatches(f, '', typeFilter))
  }
  const q = query.toLowerCase()
  if (pref.name.toLowerCase().includes(q) || pref.region.toLowerCase().includes(q)) {
    return typeFilter === 'all' || pref.facts.some((f) => f.type === typeFilter)
  }
  return pref.facts.some((f) => factMatches(f, query, typeFilter))
}

function PrefDetail({
  pref,
  typeLabels,
  typeOrder,
  typeFilter,
  query,
}: {
  pref: GeographyPrefecture
  typeLabels: Record<string, string>
  typeOrder: GeographyFactType[]
  typeFilter: GeographyFactType | 'all'
  query: string
}) {
  const byType = useMemo(() => {
    const facts = pref.facts.filter((f) => factMatches(f, query, typeFilter))
    const map = new Map<string, GeographyFact[]>()
    for (const t of typeOrder) {
      map.set(t, [])
    }
    for (const f of facts) {
      const list = map.get(f.type) ?? []
      list.push(f)
      map.set(f.type, list)
    }
    return {
      facts,
      sections: [...map.entries()].filter(([, list]) => list.length > 0),
    }
  }, [pref, query, typeFilter, typeOrder])

  if (byType.facts.length === 0) {
    return (
      <p className="text-sm text-muted">
        この条件に合う項目はありません。検索や種別フィルタを変えてみてください。
      </p>
    )
  }

  return (
    <div className="space-y-5">
      {byType.sections.map(([type, list]) => (
        <section key={type}>
          <h3 className="mb-2 text-sm font-bold text-brand">
            {typeLabels[type] ?? type}
            <span className="ml-2 font-medium text-muted">{list.length}</span>
          </h3>
          <ul className="space-y-2">
            {list.map((f) => (
              <li
                key={`${f.type}-${f.label}`}
                className="rounded-xl border border-gray-200 bg-white px-3 py-2.5"
              >
                <p className="text-sm font-semibold text-gray-900">{f.label}</p>
                {f.hooks.length > 0 && (
                  <p className="mt-1 text-xs leading-relaxed text-muted">
                    {f.hooks.join(' · ')}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  )
}

export function GeographyPage() {
  const [data, setData] = useState<GeographyData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<GeographyFactType | 'all'>('all')
  const [regionFilter, setRegionFilter] = useState<string>('all')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const geo = await fetchGeography()
        if (cancelled) return
        setData(geo)
        const first = geo.prefectures.find((p) => p.facts.length > 0)
        setSelectedId(first?.id ?? geo.prefectures[0]?.id ?? null)
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

  const typeLabels = useMemo(() => {
    const map: Record<string, string> = {}
    for (const t of data?.types ?? []) map[t.id] = t.label
    return map
  }, [data])

  const typeOrder = useMemo(
    () => (data?.types.map((t) => t.id) ?? []) as GeographyFactType[],
    [data],
  )

  const filteredPrefs = useMemo(() => {
    if (!data) return []
    return data.prefectures.filter((p) => {
      if (regionFilter !== 'all' && p.region !== regionFilter) return false
      if (query || typeFilter !== 'all') return prefMatches(p, query, typeFilter)
      return true
    })
  }, [data, query, typeFilter, regionFilter])

  const selected =
    filteredPrefs.find((p) => p.id === selectedId) ?? filteredPrefs[0] ?? null

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

  const totalFacts = data.prefectures.reduce((n, p) => n + p.facts.length, 0)

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 pb-20">
      <div className="mb-6">
        <Link
          to="/"
          className="text-sm font-medium text-brand hover:text-brand-hover"
        >
          ← ホーム
        </Link>
      </div>

      <header className="mb-6">
        <p className="mb-1 text-sm font-medium text-brand">国内旅行実務</p>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-gray-900">
              観光地理ドリル
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              過去問解説から整理した都道府県別の名所・温泉・祭り・特産など（
              {totalFacts}
              項目）。県を選んで集中暗記、種別・検索で横断復習できます。
            </p>
          </div>
          <Link
            to="/study/geography/cards"
            className="inline-flex shrink-0 items-center rounded-xl bg-brand px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-hover"
          >
            フラッシュカード →
          </Link>
        </div>
      </header>

      <div className="mb-4 flex flex-col gap-3">
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="キーワード（例: 御柱、三朝、千枚漬）"
          className="w-full rounded-xl border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none ring-brand focus:ring-2"
        />
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

      <div className="grid gap-4 lg:grid-cols-[240px_1fr]">
        <aside className="max-h-[70vh] overflow-y-auto rounded-2xl border border-gray-200 bg-white p-2 lg:max-h-[calc(100dvh-12rem)]">
          <p className="px-2 py-1.5 text-xs font-semibold text-muted">
            都道府県（{filteredPrefs.length}）
          </p>
          <ul className="flex flex-col gap-0.5">
            {filteredPrefs.map((p) => {
              const count = p.facts.filter((f) =>
                factMatches(f, query, typeFilter),
              ).length
              const active = selected?.id === p.id
              return (
                <li key={p.id}>
                  <button
                    type="button"
                    onClick={() => setSelectedId(p.id)}
                    className={`flex w-full items-center justify-between rounded-lg px-2.5 py-2 text-left text-sm ${
                      active
                        ? 'bg-brand-soft font-semibold text-brand'
                        : 'text-gray-800 hover:bg-gray-50'
                    }`}
                  >
                    <span>{p.name}</span>
                    <span className="tabular-nums text-xs text-muted">
                      {count}
                    </span>
                  </button>
                </li>
              )
            })}
          </ul>
        </aside>

        <main className="rounded-2xl border border-gray-200 bg-surface/60 p-4 sm:p-5">
          {selected ? (
            <>
              <div className="mb-4 flex items-baseline justify-between gap-2 border-b border-gray-200 pb-3">
                <div>
                  <p className="text-xs font-medium text-muted">
                    {selected.region}
                  </p>
                  <h2 className="text-xl font-bold text-gray-900">
                    {selected.name}
                  </h2>
                </div>
                <p className="text-sm text-muted">
                  {
                    selected.facts.filter((f) =>
                      factMatches(f, query, typeFilter),
                    ).length
                  }{' '}
                  項目
                </p>
              </div>
              <PrefDetail
                pref={selected}
                typeLabels={typeLabels}
                typeOrder={typeOrder}
                typeFilter={typeFilter}
                query={query}
              />
            </>
          ) : (
            <p className="text-sm text-muted">該当する都道府県がありません。</p>
          )}
        </main>
      </div>
    </div>
  )
}

