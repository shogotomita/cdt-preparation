export function FilterChip({
  active,
  onClick,
  label,
}: {
  active: boolean
  onClick: () => void
  label: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-3 py-1 text-xs font-medium ${
        active
          ? 'bg-brand text-white'
          : 'bg-white text-gray-700 ring-1 ring-gray-200 hover:bg-gray-50'
      }`}
    >
      {label}
    </button>
  )
}
