import { useQuery } from '@tanstack/react-query'
import clsx from 'clsx'
import { Check } from 'lucide-react'
import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError, api } from '@/api/client'
import type { Draft, FieldRaw, Values } from '@/api/types'
import { ErrorNote, PageHeader, Spinner } from '@/components/ui'
import { BuildingOverlay } from './BuildingOverlay'
import { DescribeStep } from './DescribeStep'
import { ParametersStep } from './ParametersStep'

const STEPS = ['Описание', 'Параметры', 'Пакет выпуска']

function Stepper({ current }: { current: number }) {
  return (
    <ol className="mb-6 flex items-center gap-3 text-sm">
      {STEPS.map((label, index) => (
        <li key={label} className="flex items-center gap-3">
          <span
            className={clsx(
              'flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold',
              index < current && 'bg-brand-700 text-white',
              index === current && 'bg-brand-50 text-brand-800 ring-2 ring-brand-600',
              index > current && 'bg-ink-100 text-ink-500',
            )}
          >
            {index < current ? <Check className="h-4 w-4" /> : index + 1}
          </span>
          <span className={clsx('font-medium', index <= current ? 'text-ink-900' : 'text-ink-400')}>{label}</span>
          {index < STEPS.length - 1 && <span className="h-px w-10 bg-ink-200" />}
        </li>
      ))}
    </ol>
  )
}

export function NewIssuePage() {
  const navigate = useNavigate()
  const meta = useQuery({ queryKey: ['meta'], queryFn: api.meta })
  const templates = useQuery({ queryKey: ['templates'], queryFn: api.templates })
  const [text, setText] = useState('')
  const [inn, setInn] = useState('')
  const [draft, setDraft] = useState<Draft | null>(null)
  const [values, setValues] = useState<Values>({})
  const [templateId, setTemplateId] = useState('decision_coupon')
  const [parsing, setParsing] = useState(false)
  const [building, setBuilding] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const startedAt = useRef<string | null>(null)

  if (meta.isLoading) return <Spinner />
  if (!meta.data) return <ErrorNote>Сервис недоступен. Проверьте, что backend запущен.</ErrorNote>

  const parse = async () => {
    startedAt.current ??= new Date().toISOString()
    setParsing(true)
    setError(null)
    try {
      const result = await api.draft(text, inn)
      setDraft(result)
      setValues(result.values)
      setFieldErrors({})
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Не удалось разобрать описание')
    } finally {
      setParsing(false)
    }
  }

  const change = (key: string, value: FieldRaw) => {
    setValues((current) => ({ ...current, [key]: { value, origin: 'answer', evidence: null } }))
    setFieldErrors(({ [key]: _, ...rest }) => rest)
  }

  const build = async () => {
    if (!draft) return
    setBuilding(true)
    setError(null)
    try {
      const filled = Object.fromEntries(
        Object.entries(values).filter(([, item]) => item.value !== '' && item.value !== null && item.value !== undefined),
      )
      const issue = await api.createIssue({
        text,
        values: filled,
        template_id: templateId,
        started_at: startedAt.current ?? new Date().toISOString(),
        questions_asked: draft.questions.length,
      })
      navigate(`/issues/${issue.id}`, { state: { fresh: true } })
    } catch (reason) {
      if (reason instanceof ApiError) {
        setFieldErrors(reason.fields)
        setError(Object.keys(reason.fields).length ? 'Проверьте отмеченные параметры' : reason.message)
      } else {
        setError('Не удалось сформировать пакет')
      }
    } finally {
      setBuilding(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Новый выпуск ЦФА"
        subtitle="От описания условий до решения о выпуске и проверенного смарт-контракта за несколько минут"
      />
      <Stepper current={draft ? 1 : 0} />
      {!draft ? (
        <>
          {error && <div className="mb-4"><ErrorNote>{error}</ErrorNote></div>}
          <DescribeStep
            meta={meta.data}
            text={text}
            inn={inn}
            loading={parsing}
            onText={(value) => {
              startedAt.current ??= new Date().toISOString()
              setText(value)
            }}
            onInn={setInn}
            onSubmit={parse}
          />
        </>
      ) : (
        <ParametersStep
          meta={meta.data}
          draft={draft}
          text={text}
          values={values}
          templates={templates.data ?? []}
          templateId={templateId}
          errors={fieldErrors}
          error={error}
          building={building}
          onChange={change}
          onTemplate={setTemplateId}
          onBack={() => setDraft(null)}
          onSubmit={build}
        />
      )}
      {building && <BuildingOverlay />}
    </>
  )
}
