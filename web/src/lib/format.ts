const rub = new Intl.NumberFormat('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const whole = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 })

export function money(value: string | number): string {
  return rub.format(Number(value))
}

export function amount(value: string | number): string {
  const number = Number(value)
  if (number >= 1e9) return `${trim(number / 1e9)} млрд ₽`
  if (number >= 1e6) return `${trim(number / 1e6)} млн ₽`
  return `${whole.format(number)} ₽`
}

function trim(value: number): string {
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(value)
}

export function integer(value: number): string {
  return whole.format(value)
}

export function percent(fraction: string | number, digits = 2): string {
  return `${(Number(fraction) * 100).toFixed(digits).replace('.', ',')}%`
}

export function date(value: string): string {
  const [year, month, day] = value.slice(0, 10).split('-')
  return `${day}.${month}.${year}`
}

export function dateTime(value: string): string {
  return new Date(value).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function duration(seconds: number | null | undefined): string {
  if (seconds == null) return '—'
  if (seconds < 60) return `${Math.round(seconds)} с`
  const minutes = Math.floor(seconds / 60)
  const rest = Math.round(seconds % 60)
  if (minutes < 60) return rest ? `${minutes} мин ${rest} с` : `${minutes} мин`
  return `${Math.floor(minutes / 60)} ч ${minutes % 60} мин`
}

export function months(term: number): string {
  if (term % 12 === 0) {
    const years = term / 12
    return `${years} ${plural(years, ['год', 'года', 'лет'])}`
  }
  return `${term} ${plural(term, ['месяц', 'месяца', 'месяцев'])}`
}

export function plural(value: number, forms: [string, string, string]): string {
  const tail = value % 100
  if (tail >= 11 && tail <= 14) return forms[2]
  if (value % 10 === 1) return forms[0]
  if (value % 10 >= 2 && value % 10 <= 4) return forms[1]
  return forms[2]
}

export const FREQUENCY: Record<string, string> = {
  monthly: 'ежемесячно',
  quarterly: 'ежеквартально',
  semiannual: 'раз в полгода',
  annual: 'раз в год',
  at_maturity: 'в дату погашения',
}

export const INVESTORS: Record<string, string> = {
  qualified_only: 'Только квалифицированные',
  all: 'Все инвесторы',
}
