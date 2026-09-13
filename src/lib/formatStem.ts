/**
 * Insert structural line breaks into quiz stems that were stored as a single line.
 * Idempotent: already-formatted stems (newline before markers) are left alone.
 */
export function formatStem(stem: string): string {
  let s = stem.replaceAll('＜図＞', '<図>')

  // Paragraph after the lead-in question cue
  s = s.replace(/(選びなさい[。．])(?!\n)/g, '$1\n\n')

  // Notes: （注1）… / （注）…
  s = s.replace(/(?<!\n)(?=[（(]注[0-9一二三四五六七八九十]*[）)])/g, '\n')

  // Section headers
  s = s.replace(/(?<!\n)(?=[＜<](?:行程|資料|図)[＞>])/g, '\n\n')
  s = s.replace(/([＜<](?:行程|資料|図)[＞>])(?!\n)/g, '$1\n')
  s = s.replace(/(?<!\n)(?=<図>)/g, '\n\n')
  s = s.replace(/(<図>)(?!\n)/g, '$1\n')

  // Circled list items after sentence end / section close (not mid-phrase refs like は①と同じ)
  s = s.replace(/(?<=[。．＞>])(?=[①-⑩])/g, '\n')

  // Itinerary day bullets
  s = s.replace(
    /(?<!\n)(?=・(?:[0-9一二三四五六七八九十]+日|[12]日にわたる))/g,
    '\n',
  )

  // Material subsections
  s = s.replace(/(?<!\n)(?=●)/g, '\n\n')

  if (/[＜<]資料[＞>]|●/.test(s)) {
    for (const lab of [
      '基本宿泊料',
      'サービス料',
      '消費税',
      '入湯税',
      'チェックイン',
      'チェックアウト',
    ]) {
      s = s.replace(new RegExp(`(?<!\\n)(?=${lab}：)`, 'g'), '\n')
    }
    // Longer labels where "：" is not immediately after the keyword
    s = s.replace(/(?<!\n)(?=宿泊契約解除)/g, '\n')
  }

  s = s.replace(/\n{3,}/g, '\n\n')
  return s.trim()
}
