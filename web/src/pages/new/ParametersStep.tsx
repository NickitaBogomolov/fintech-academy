import clsx from 'clsx'
import { ArrowLeft, Building2, CheckCircle2, CircleHelp, Pencil, Rocket } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { Draft, FieldDef, FieldRaw, Meta, TemplateInfo, Values } from '@/api/types'
import { OriginChip } from '@/components/status'
import { Button, Card, CardHeader, ErrorNote } from '@/components/ui'
import { FieldInput, displayValue } from './FieldInput'

interface Props {
  meta: Meta
  draft: Draft
  text: string
  values: Values
  templates: TemplateInfo[]
  templateId: string
  errors: Record<string, string>
  error: string | null
  building: boolean
  onChange: (key: string, value: FieldRaw) => void
  onTemplate: (id: string) => void
  onBack: () => void
  onSubmit: () => void
}

function isFilled(value: FieldRaw | undefined): boolean {
  return value !== undefined && value !== null && value !== ''
}

function Highlighted({ text, values, fields }: { text: string; values: Values; fields: FieldDef[] }) {
  const parts = useMemo(() => {
    const spans: { start: number; end: number; label: string }[] = []
    const lower = text.toLowerCase()
    for (const field of fields) {
      const evidence = values[field.key]?.origin === 'text' ? values[field.key]?.evidence : null
      if (!evidence) continue
      const start = lower.indexOf(evidence.toLowerCase())
      if (start >= 0 && !spans.some((span) => start < span.end && start + evidence.length > span.start)) {
        spans.push({ start, end: start + evidence.length, label: field.label })
      }
    }
    spans.sort((a, b) => a.start - b.start)
    const result: { text: string; label?: string }[] = []
    let position = 0
    for (const span of spans) {
      if (span.start > position) result.push({ text: text.slice(position, span.start) })
      result.push({ text: text.slice(span.start, span.end), label: span.label })
      position = span.end
    }
    if (position < text.length) result.push({ text: text.slice(position) })
    return result
  }, [text, values, fields])

  return (
    <p className="text-sm leading-7 text-ink-700">
      {parts.map((part, index) =>
        part.label ? (
          <mark key={index} title={part.label} className="rounded bg-brand-100 px-1 py-0.5 text-brand-900">
            {part.text}
          </mark>
        ) : (
          <span key={index}>{part.text}</span>
        ),
      )}
    </p>
  )
}

export function ParametersStep(props: Props) {
  const { meta, draft, text, values, templates, templateId, errors, error, building, onChange } = props
  const [editing, setEditing] = useState<string | null>(null)
  const fieldsByKey = Object.fromEntries(meta.fields.map((field) => [field.key, field]))
  const questionKeys = draft.questions.map((question) => question.key)
  const unanswered = questionKeys.filter((key) => !isFilled(values[key]?.value))
  const counts = {
    text: Object.values(values).filter((item) => item.origin === 'text').length,
    default: Object.values(values).filter((item) => item.origin === 'default').length,
    answer: Object.values(values).filter((item) => item.origin === 'answer' && isFilled(item.value)).length,
  }
  const total = meta.fields.length
  const issuer = meta.issuers.find((item) => item.inn === values.issuer_inn?.value)

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
      <div className="space-y-6">
        <Card className="p-5">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <div className="text-[15px] font-semibold text-ink-900">
              Из описания извлечено {counts.text} из {total} параметров
            </div>
            <div className="text-sm text-ink-500">
              {unanswered.length ? `Осталось уточнить: ${unanswered.length}` : 'Все параметры заполнены'}
            </div>
          </div>
          <div className="mt-3 flex h-2.5 gap-0.5 overflow-hidden rounded-full bg-ink-100">
            <div className="bg-series-1" style={{ width: `${(counts.text / total) * 100}%` }} />
            <div className="bg-green-600" style={{ width: `${(counts.answer / total) * 100}%` }} />
            <div className="bg-ink-300" style={{ width: `${(counts.default / total) * 100}%` }} />
          </div>
          <div className="mt-2 flex flex-wrap gap-4 text-xs text-ink-600">
            <span className="flex items-center gap-1.5">
              <i className="h-2 w-2 rounded-full bg-series-1" />
              из описания {counts.text}
            </span>
            <span className="flex items-center gap-1.5">
              <i className="h-2 w-2 rounded-full bg-green-600" />
              уточнено {counts.answer}
            </span>
            <span className="flex items-center gap-1.5">
              <i className="h-2 w-2 rounded-full bg-ink-300" />
              по умолчанию {counts.default}
            </span>
          </div>
          {draft.notes.map((note) => (
            <p key={note} className="mt-3 text-sm text-warn">
              {note}
            </p>
          ))}
        </Card>

        {draft.questions.length > 0 && (
          <Card>
            <CardHeader
              title="Нужно уточнить"
              subtitle="Этих условий нет в описании, а без них решение о выпуске будет неполным"
            />
            <div className="divide-y divide-ink-100">
              {draft.questions.map((question) => {
                const answered = isFilled(values[question.key]?.value)
                return (
                  <div key={question.key} className={clsx('px-5 py-4', errors[question.key] && 'bg-red-50/50')}>
                    <div className="mb-3 flex items-start gap-2.5">
                      {answered ? (
                        <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-good" />
                      ) : (
                        <CircleHelp className="mt-0.5 h-5 w-5 shrink-0 text-brand-600" />
                      )}
                      <div>
                        <div className="text-sm font-medium text-ink-900">{question.text}</div>
                        {question.hint && <div className="mt-0.5 text-xs text-ink-500">{question.hint}</div>}
                      </div>
                    </div>
                    <div className="pl-7">
                      <FieldInput
                        kind={question.kind}
                        fieldKey={question.key}
                        value={values[question.key]?.value}
                        choices={question.choices}
                        issuers={meta.issuers}
                        onChange={(value) => onChange(question.key, value)}
                      />
                      {errors[question.key] && <p className="mt-2 text-xs text-bad">{errors[question.key]}</p>}
                    </div>
                  </div>
                )
              })}
            </div>
          </Card>
        )}

        <Card>
          <CardHeader title="Параметры выпуска" subtitle="Любое значение можно поправить вручную" />
          {meta.groups.map((group) => (
            <div key={group} className="border-b border-ink-100 last:border-0">
              <div className="bg-ink-50/60 px-5 py-2 text-xs font-semibold uppercase tracking-wide text-ink-500">{group}</div>
              {meta.fields
                .filter((field) => field.group === group)
                .map((field) => {
                  const item = values[field.key]
                  const isEditing = editing === field.key
                  return (
                    <div
                      key={field.key}
                      className={clsx('grid gap-2 px-5 py-3 sm:grid-cols-[220px_1fr_auto] sm:items-center', errors[field.key] && 'bg-red-50/50')}
                    >
                      <div className="text-sm text-ink-600">{field.label}</div>
                      <div className="min-w-0">
                        {isEditing ? (
                          <FieldInput
                            kind={field.kind}
                            fieldKey={field.key}
                            value={item?.value}
                            choices={field.choices}
                            issuers={meta.issuers}
                            onChange={(value) => onChange(field.key, value)}
                          />
                        ) : (
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-sm font-medium tabular-nums text-ink-900">
                              {displayValue(field.kind, item?.value, fieldsByKey[field.key]?.choices ?? [])}
                            </span>
                            {item && isFilled(item.value) && <OriginChip origin={item.origin} />}
                          </div>
                        )}
                        {errors[field.key] && <p className="mt-1 text-xs text-bad">{errors[field.key]}</p>}
                      </div>
                      <button
                        type="button"
                        onClick={() => setEditing(isEditing ? null : field.key)}
                        className="justify-self-start rounded-md p-1.5 text-ink-400 hover:bg-ink-100 hover:text-ink-700 sm:justify-self-end"
                        aria-label={isEditing ? 'Готово' : 'Изменить'}
                      >
                        {isEditing ? <CheckCircle2 className="h-4 w-4" /> : <Pencil className="h-4 w-4" />}
                      </button>
                    </div>
                  )
                })}
            </div>
          ))}
        </Card>
      </div>

      <div className="space-y-6 lg:sticky lg:top-8 lg:h-fit">
        <Card className="p-5">
          <div className="text-xs font-semibold uppercase tracking-wide text-ink-500">Описание</div>
          <div className="mt-2">
            <Highlighted text={text} values={values} fields={meta.fields} />
          </div>
          <div className="mt-3 text-xs text-ink-500">Подсвечены фрагменты, из которых взяты параметры. {draft.provider === 'rules' ? 'Разбор правилами, без внешних вызовов.' : ''}</div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-ink-500">
            <Building2 className="h-4 w-4" />
            Эмитент
          </div>
          {issuer ? (
            <div className="mt-2 space-y-1 text-sm">
              <div className="font-medium text-ink-900">{issuer.short_name}</div>
              <div className="text-ink-500">ОГРН {issuer.ogrn}</div>
              <div className="text-ink-500">{issuer.address}</div>
              <div className="text-ink-500">Рейтинг: {issuer.rating ?? 'нет'}</div>
              <div className="pt-1">
                <OriginChip origin="registry" />
              </div>
            </div>
          ) : (
            <p className="mt-2 text-sm text-ink-500">Выберите эмитента в вопросах слева</p>
          )}
        </Card>

        <Card className="p-5">
          <label htmlFor="template" className="text-xs font-semibold uppercase tracking-wide text-ink-500">
            Шаблон решения о выпуске
          </label>
          <select id="template" value={templateId} onChange={(event) => props.onTemplate(event.target.value)} className="field-input mt-2">
            {templates.map((template) => (
              <option key={template.id} value={template.id}>
                {template.title}
              </option>
            ))}
          </select>
          {error && <div className="mt-4"><ErrorNote>{error}</ErrorNote></div>}
          <Button
            size="lg"
            className="mt-4 w-full"
            onClick={props.onSubmit}
            loading={building}
            disabled={unanswered.length > 0}
            icon={<Rocket className="h-4 w-4" />}
          >
            Сформировать пакет выпуска
          </Button>
          {unanswered.length > 0 && <p className="mt-2 text-center text-xs text-ink-500">Ответьте на вопросы слева</p>}
          <Button variant="ghost" className="mt-2 w-full" onClick={props.onBack} icon={<ArrowLeft className="h-4 w-4" />}>
            Изменить описание
          </Button>
        </Card>
      </div>
    </div>
  )
}
