import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import { Eye, FileUp, LayoutTemplate, Plus, Save, Trash2 } from 'lucide-react'
import { type ChangeEvent, useState } from 'react'
import { api } from '@/api/client'
import type { TemplateInfo } from '@/api/types'
import { CodeView } from '@/components/CodeView'
import { Markdown } from '@/components/Markdown'
import { Button, Card, CardHeader, ErrorNote, PageHeader, Pill, Spinner } from '@/components/ui'

const VARIABLES = [
  ['spec.nominal', 'номинал'],
  ['spec.price', 'цена размещения'],
  ['spec.min_quantity / max_quantity', 'количество ЦФА'],
  ['spec.issue_date / maturity_date', 'даты'],
  ['spec.coupon_rate', 'ставка, доля'],
  ['spec.coupon_frequency', 'периодичность'],
  ['spec.investors', 'круг инвесторов'],
  ['issuer.*', 'реквизиты эмитента'],
  ['schedule.periods', 'график выплат'],
  ['operator.*', 'оператор ИС'],
]

const FILTERS = ['money', 'money_words', 'int_words', 'percent', 'percent_words', 'date_ru', 'date_words', 'frequency_label']

function TemplateView({ template, onDelete }: { template: TemplateInfo; onDelete: () => void }) {
  return (
    <Card>
      <CardHeader
        title={template.title}
        subtitle={template.description || 'Без описания'}
        action={
          template.builtin ? (
            <Pill tone="brand">встроенный</Pill>
          ) : (
            <Button variant="danger" size="sm" icon={<Trash2 className="h-4 w-4" />} onClick={onDelete}>
              Удалить
            </Button>
          )
        }
      />
      <div className="space-y-4 p-5">
        <div>
          <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-500">Поля, которые подставляются</div>
          <div className="flex flex-wrap gap-1.5">
            {template.variables.map((variable) => (
              <code key={variable} className="rounded bg-brand-50 px-1.5 py-0.5 font-mono text-xs text-brand-800">
                {variable}
              </code>
            ))}
          </div>
        </div>
        <CodeView code={template.source} language="markdown" maxHeight={520} />
      </div>
    </Card>
  )
}

function TemplateEditor({ initial, onSaved }: { initial: string; onSaved: (id: string) => void }) {
  const queryClient = useQueryClient()
  const [id, setId] = useState('')
  const [source, setSource] = useState(initial)
  const [preview, setPreview] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const previewMutation = useMutation({
    mutationFn: () => api.previewTemplate(source),
    onSuccess: (result) => {
      setPreview(result.document)
      setError(null)
    },
    onError: (reason: Error) => setError(reason.message),
  })
  const saveMutation = useMutation({
    mutationFn: () => api.saveTemplate(id, source),
    onSuccess: (template) => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      onSaved(template.id)
    },
    onError: (reason: Error) => setError(reason.message),
  })

  const upload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    setSource(await file.text())
    setId(file.name.replace(/\.md\.j2$|\.md$|\.txt$/, '').toLowerCase().replace(/[^a-z0-9_-]/g, '-'))
  }

  return (
    <Card>
      <CardHeader
        title="Новый шаблон"
        subtitle="Юридический текст остаётся как есть, меняются только поля в фигурных скобках"
        action={
          <label className="inline-flex h-8 cursor-pointer items-center gap-2 rounded-lg border border-ink-200 bg-white px-3 text-sm font-medium text-ink-800 hover:bg-ink-50">
            <FileUp className="h-4 w-4" />
            Загрузить файл
            <input type="file" accept=".j2,.md,.txt" className="hidden" onChange={upload} />
          </label>
        }
      />
      <div className="space-y-4 p-5">
        <div className="grid gap-4 sm:grid-cols-[1fr_auto] sm:items-end">
          <div>
            <label htmlFor="template-id" className="text-sm font-medium text-ink-800">
              Идентификатор
            </label>
            <input
              id="template-id"
              className="field-input mt-1.5 font-mono"
              placeholder="bank-decision-v2"
              value={id}
              onChange={(event) => setId(event.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" icon={<Eye className="h-4 w-4" />} loading={previewMutation.isPending} onClick={() => previewMutation.mutate()}>
              Предпросмотр
            </Button>
            <Button icon={<Save className="h-4 w-4" />} loading={saveMutation.isPending} disabled={id.length < 3} onClick={() => saveMutation.mutate()}>
              Сохранить
            </Button>
          </div>
        </div>
        <textarea
          value={source}
          onChange={(event) => setSource(event.target.value)}
          rows={18}
          spellCheck={false}
          className="w-full rounded-lg border border-ink-200 bg-ink-50 p-3 font-mono text-xs leading-5 outline-none focus:border-brand-500 focus:ring-4 focus:ring-brand-100"
        />
        {error && <ErrorNote>{error}</ErrorNote>}
        {preview && (
          <div className="rounded-lg border border-ink-200 bg-white px-6 py-8">
            <div className="mb-4 text-xs font-semibold uppercase tracking-wide text-ink-500">Предпросмотр на тестовом выпуске</div>
            <Markdown>{preview}</Markdown>
          </div>
        )}
      </div>
    </Card>
  )
}

export function TemplatesPage() {
  const queryClient = useQueryClient()
  const templates = useQuery({ queryKey: ['templates'], queryFn: api.templates })
  const [selected, setSelected] = useState<string>('decision_coupon')
  const [creating, setCreating] = useState(false)

  const remove = useMutation({
    mutationFn: (id: string) => api.deleteTemplate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      setSelected('decision_coupon')
    },
  })

  if (templates.isLoading) return <Spinner />
  const list = templates.data ?? []
  const current = list.find((template) => template.id === selected) ?? list[0]

  return (
    <>
      <PageHeader
        title="Шаблоны решений о выпуске"
        subtitle="Оператор загружает свою форму документа один раз. Дальше каждый выпуск заполняется по ней автоматически"
        action={
          <Button icon={<Plus className="h-4 w-4" />} onClick={() => setCreating(true)}>
            Новый шаблон
          </Button>
        }
      />
      <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
        <div className="space-y-3">
          {list.map((template) => (
            <button
              key={template.id}
              type="button"
              onClick={() => {
                setSelected(template.id)
                setCreating(false)
              }}
              className={clsx(
                'w-full rounded-xl border bg-white p-4 text-left shadow-card transition-colors',
                !creating && current?.id === template.id ? 'border-brand-600 ring-1 ring-brand-600' : 'border-ink-200 hover:border-ink-300',
              )}
            >
              <div className="flex items-center gap-2">
                <LayoutTemplate className="h-4 w-4 text-brand-700" />
                <span className="text-sm font-medium text-ink-900">{template.title}</span>
              </div>
              <div className="mt-1 font-mono text-xs text-ink-500">{template.id}</div>
              <div className="mt-2 text-xs text-ink-500">Полей: {template.variables.length}</div>
            </button>
          ))}
          <Card className="p-4">
            <div className="text-xs font-semibold uppercase tracking-wide text-ink-500">Разметка</div>
            <p className="mt-2 text-xs text-ink-600">
              Поле: <code className="font-mono">{'{{ spec.nominal | money_words }}'}</code>. Условие:{' '}
              <code className="font-mono">{'{% if spec.early_redemption %}…{% endif %}'}</code>
            </p>
            <dl className="mt-3 space-y-1 text-xs">
              {VARIABLES.map(([name, label]) => (
                <div key={name} className="flex justify-between gap-2">
                  <dt className="font-mono text-ink-700">{name}</dt>
                  <dd className="text-right text-ink-500">{label}</dd>
                </div>
              ))}
            </dl>
            <div className="mt-3 text-xs text-ink-500">Форматы: {FILTERS.join(', ')}</div>
          </Card>
        </div>
        <div>
          {creating ? (
            <TemplateEditor
              initial={list.find((template) => template.builtin)?.source ?? ''}
              onSaved={(id) => {
                setSelected(id)
                setCreating(false)
              }}
            />
          ) : (
            current && <TemplateView template={current} onDelete={() => remove.mutate(current.id)} />
          )}
        </div>
      </div>
    </>
  )
}
