import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { FilterChip } from '../components/FilterChip'
import { fetchNumbers } from '../lib/data'
import type {
  NumbersCategoryId,
  NumbersCategoryMeta,
  NumbersData,
  NumbersItem,
  SubjectId,
} from '../types'

const SUBJECT_LABELS: Record<SubjectId, string> = {
  hou: '旅行業法',
  yakkan: '約款',
  jitsumu: '実務',
}

function itemMatches(
  item: NumbersItem,
  query: string,
  subjectFilter: SubjectId | 'all',
  categoryMeta: Map<NumbersCategoryId, NumbersCategoryMeta>,
): boolean {
  if (subjectFilter !== 'all') {
    const cat = categoryMeta.get(item.category)
    if (!cat || cat.subject !== subjectFilter) return false
  }
  if (!query) return true
  const q = query.toLowerCase()
  if (item.title.toLowerCase().includes(q)) return true
  if (item.bullets.some((b) => b.toLowerCase().includes(q))) return true
  if (item.traps?.some((t) => t.toLowerCase().includes(q))) return true
  return false
}

function CategoryDetail({
  items,
}: {
  items: NumbersItem[]
}) {
  if (items.length === 0) {
    return (
      <p className="text-sm text-muted">
        この条件に合う項目はありません。検索や科目フィルタを変えてみてください。
      </p>
    )
  }

  return (
    <div className="space-y-4">
      {items.map((item) => (
        <article
          key={item.id}
          className="rounded-xl border border-gray-200 bg-white px-3 py-3 sm:px-4"
        >
          <h3 className="text-sm font-bold text-gray-900">{item.title}</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-relaxed text-gray-800">
            {item.bullets.map((b) => (
              <li key={b}>{b}</li>
            ))}
          </ul>
          {item.traps && item.traps.length > 0 && (
            <div className="mt-3 rounded-lg bg-amber-50 px-3 py-2">
              <p className="text-xs font-semibold text-amber-900">ひっかけ</p>
              <ul className="mt-1 list-disc space-y-0.5 pl-4 text-xs leading-relaxed text-amber-950">
                {item.traps.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            </div>
          )}
        </article>
      ))}
    </div>
  )
}

export function NumbersPage() {
  const [data, setData] = useState<NumbersData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [subjectFilter, setSubjectFilter] = useState<SubjectId | 'all'>('all')
  const [selectedId, setSelectedId] = useState<NumbersCategoryId | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const nums = await fetchNumbers()
        if (cancelled) return
        setData(nums)
        setSelectedId(nums.categories[0]?.id ?? null)
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

  const categoryMeta = useMemo(() => {
    const map = new Map<NumbersCategoryId, NumbersCategoryMeta>()
    for (const c of data?.categories ?? []) map.set(c.id, c)
    return map
  }, [data])

  const filteredCategories = useMemo(() => {
    if (!data) return []
    return data.categories.filter((c) => {
      if (subjectFilter !== 'all' && c.subject !== subjectFilter) return false
      const count = data.items.filter(
        (item) =>
          item.category === c.id &&
          itemMatches(item, query, subjectFilter, categoryMeta),
      ).length
      if (query) return count > 0
      return true
    })
  }, [data, query, subjectFilter, categoryMeta])

  const selected =
    filteredCategories.find((c) => c.id === selectedId) ??
    filteredCategories[0] ??
    null

  const selectedItems = useMemo(() => {
    if (!data || !selected) return []
    return data.items.filter(
      (item) =>
        item.category === selected.id &&
        itemMatches(item, query, subjectFilter, categoryMeta),
    )
  }, [data, selected, query, subjectFilter, categoryMeta])

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
        <p className="mb-1 text-sm font-medium text-brand">数字・期限・金額</p>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-gray-900">
              数字暗記ドリル
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              過去問解説から整理した登録期限・補償額・JR／ANA運賃ルールなど（
              {data.items.length}
              項目）。カテゴリを選んで集中暗記、科目・検索で横断復習できます。
            </p>
          </div>
          <Link
            to="/study/numbers/cards"
            className="inline-flex shrink-0 items-center rounded-xl bg-brand px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-hover"
          >
            数字フラッシュカード →
          </Link>
        </div>
      </header>

      <div className="mb-4 flex flex-col gap-3">
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="キーワード（例: 15％、30日、SUPER VALUE）"
          className="w-full rounded-xl border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none ring-brand focus:ring-2"
        />
        <div className="flex flex-wrap gap-1.5">
          <FilterChip
            active={subjectFilter === 'all'}
            onClick={() => setSubjectFilter('all')}
            label="すべて"
          />
          {(['hou', 'yakkan', 'jitsumu'] as SubjectId[]).map((s) => (
            <FilterChip
              key={s}
              active={subjectFilter === s}
              onClick={() => setSubjectFilter(s)}
              label={SUBJECT_LABELS[s]}
            />
          ))}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[240px_1fr]">
        <aside className="max-h-[70vh] overflow-y-auto rounded-2xl border border-gray-200 bg-white p-2 lg:max-h-[calc(100dvh-12rem)]">
          <p className="px-2 py-1.5 text-xs font-semibold text-muted">
            カテゴリ（{filteredCategories.length}）
          </p>
          <ul className="flex flex-col gap-0.5">
            {filteredCategories.map((c) => {
              const count = data.items.filter(
                (item) =>
                  item.category === c.id &&
                  itemMatches(item, query, subjectFilter, categoryMeta),
              ).length
              const active = selected?.id === c.id
              return (
                <li key={c.id}>
                  <button
                    type="button"
                    onClick={() => setSelectedId(c.id)}
                    className={`flex w-full items-center justify-between rounded-lg px-2.5 py-2 text-left text-sm ${
                      active
                        ? 'bg-brand-soft font-semibold text-brand'
                        : 'text-gray-800 hover:bg-gray-50'
                    }`}
                  >
                    <span>{c.label}</span>
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
                    {SUBJECT_LABELS[selected.subject]}
                  </p>
                  <h2 className="text-xl font-bold text-gray-900">
                    {selected.label}
                  </h2>
                </div>
                <p className="text-sm text-muted">{selectedItems.length} 項目</p>
              </div>
              <CategoryDetail items={selectedItems} />
            </>
          ) : (
            <p className="text-sm text-muted">該当するカテゴリがありません。</p>
          )}
        </main>
      </div>
    </div>
  )
}
