import clsx from 'clsx'
import type { Choice, FieldKind, FieldRaw, Issuer } from '@/api/types'

interface Props {
  kind: FieldKind
  fieldKey: string
  value: FieldRaw | undefined
  choices: Choice[]
  issuers?: Issuer[]
  onChange: (value: FieldRaw) => void
}

const SUFFIX: Partial<Record<FieldKind, string>> = { money: '₽', percent: '%' }

function display(kind: FieldKind, value: FieldRaw | undefined): string {
  if (value === undefined || value === null) return ''
  if (kind === 'money') return new Intl.NumberFormat('ru-RU').format(Number(value))
  if (kind === 'percent') return String(value).replace('.', ',')
  return String(value)
}

function parse(kind: FieldKind, text: string): FieldRaw {
  const cleaned = text.replace(/\s/g, '').replace(',', '.')
  if (kind === 'integer') return cleaned === '' ? '' : Number.parseInt(cleaned, 10)
  if (kind === 'money' || kind === 'percent') return cleaned
  return text
}

export function FieldInput({ kind, fieldKey, value, choices, issuers, onChange }: Props) {
  if (fieldKey === 'issuer_inn' && issuers?.length) {
    return (
      <select className="field-input" value={String(value ?? '')} onChange={(event) => onChange(event.target.value)}>
        <option value="">Выберите эмитента</option>
        {issuers.map((issuer) => (
          <option key={issuer.inn} value={issuer.inn}>
            {issuer.short_name} · ИНН {issuer.inn}
          </option>
        ))}
      </select>
    )
  }

  if (kind === 'choice' || kind === 'boolean') {
    return (
      <div className="flex flex-wrap gap-2">
        {choices.map((choice) => {
          const active = String(choice.value) === String(value)
          return (
            <button
              key={String(choice.value)}
              type="button"
              onClick={() => onChange(choice.value)}
              className={clsx(
                'rounded-lg border px-3 py-2 text-sm font-medium transition-colors',
                active
                  ? 'border-brand-600 bg-brand-50 text-brand-800 ring-1 ring-brand-600'
                  : 'border-ink-200 bg-white text-ink-700 hover:border-ink-300 hover:bg-ink-50',
              )}
            >
              {choice.label}
            </button>
          )
        })}
      </div>
    )
  }

  if (kind === 'date') {
    return (
      <div className="flex flex-wrap items-center gap-2">
        {choices.map((choice) => (
          <button
            key={String(choice.value)}
            type="button"
            onClick={() => onChange(choice.value)}
            className={clsx(
              'rounded-lg border px-3 py-2 text-sm font-medium tabular-nums',
              String(choice.value) === String(value)
                ? 'border-brand-600 bg-brand-50 text-brand-800 ring-1 ring-brand-600'
                : 'border-ink-200 bg-white text-ink-700 hover:bg-ink-50',
            )}
          >
            {choice.label}
          </button>
        ))}
        <input
          type="date"
          className="field-input w-44"
          value={String(value ?? '')}
          onChange={(event) => onChange(event.target.value)}
        />
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {choices.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {choices.map((choice) => (
            <button
              key={String(choice.value)}
              type="button"
              onClick={() => onChange(choice.value)}
              className={clsx(
                'rounded-lg border px-3 py-1.5 text-sm font-medium tabular-nums',
                String(choice.value) === String(value)
                  ? 'border-brand-600 bg-brand-50 text-brand-800 ring-1 ring-brand-600'
                  : 'border-ink-200 bg-white text-ink-700 hover:bg-ink-50',
              )}
            >
              {choice.label}
            </button>
          ))}
        </div>
      )}
      <div className="relative">
        <input
          className={clsx('field-input tabular-nums', SUFFIX[kind] && 'pr-9')}
          inputMode={kind === 'text' ? 'text' : 'decimal'}
          value={display(kind, value)}
          onChange={(event) => onChange(parse(kind, event.target.value))}
        />
        {SUFFIX[kind] && (
          <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-ink-400">{SUFFIX[kind]}</span>
        )}
      </div>
    </div>
  )
}

export function displayValue(kind: FieldKind, value: FieldRaw | undefined, choices: Choice[]): string {
  if (value === undefined || value === '') return '—'
  const choice = choices.find((item) => String(item.value) === String(value))
  if (choice && (kind === 'choice' || kind === 'boolean')) return choice.label
  if (kind === 'money') return `${new Intl.NumberFormat('ru-RU').format(Number(value))} ₽`
  if (kind === 'percent') return `${String(value).replace('.', ',')}%`
  if (kind === 'date') {
    const [y, m, d] = String(value).split('-')
    return `${d}.${m}.${y}`
  }
  return String(value)
}
