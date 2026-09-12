export type FlashcardDeck = 'numbers' | 'geography'

type FlashcardKnownStore = Record<FlashcardDeck, string[]>

const STORAGE_KEY = 'cdt-flashcards-known-v1'

function emptyStore(): FlashcardKnownStore {
  return { numbers: [], geography: [] }
}

function loadStore(): FlashcardKnownStore {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return emptyStore()
    const parsed = JSON.parse(raw) as Partial<FlashcardKnownStore>
    return {
      numbers: Array.isArray(parsed.numbers) ? parsed.numbers : [],
      geography: Array.isArray(parsed.geography) ? parsed.geography : [],
    }
  } catch {
    return emptyStore()
  }
}

function saveStore(store: FlashcardKnownStore): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(store))
}

export function loadKnownIds(deck: FlashcardDeck): Set<string> {
  return new Set(loadStore()[deck])
}

export function addKnownId(deck: FlashcardDeck, id: string): Set<string> {
  const store = loadStore()
  const next = new Set(store[deck])
  next.add(id)
  store[deck] = [...next]
  saveStore(store)
  return next
}

export function clearKnownIds(
  deck: FlashcardDeck,
  idsToClear: Iterable<string>,
): Set<string> {
  const store = loadStore()
  const remove = new Set(idsToClear)
  const next = store[deck].filter((id) => !remove.has(id))
  store[deck] = next
  saveStore(store)
  return new Set(next)
}
