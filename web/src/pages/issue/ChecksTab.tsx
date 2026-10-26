import clsx from 'clsx'
import { Bug, ChevronDown, FlaskConical } from 'lucide-react'
import { useState } from 'react'
import { api } from '@/api/client'
import type { Check, CheckGroup, FaultResult, IssuePackage, Meta } from '@/api/types'
import { StatusIcon, statusLabel } from '@/components/status'
import { Card, CardHeader, ErrorNote, Pill } from '@/components/ui'

const GROUPS: { id: CheckGroup; title: string; subtitle: string }[] = [
  { id: 'arithmetic', title: 'Арифметика', subtitle: 'Объёмы, формула дохода, полнота графика' },
  { id: 'calendar', title: 'Календарь', subtitle: 'Рабочие дни и переносы выплат' },
  { id: 'regulatory', title: 'Регуляторные требования', subtitle: '259-ФЗ, 115-ФЗ, допуск инвесторов' },
  { id: 'contract', title: 'Исполнение смарт-контракта', subtitle: 'Код запускается в EVM и сравнивается с решением о выпуске' },
  { id: 'analysis', title: 'Статический анализ', subtitle: 'Поиск типовых уязвимостей' },
]

function CheckRow({ check }: { check: Check }) {
  const [open, setOpen] = useState(check.status === 'failed')
  const expandable = check.rows.length > 0
  return (
    <div className={clsx('px-5 py-3', check.status === 'failed' && 'bg-red-50/60')}>
      <button
        type="button"
        className="flex w-full items-start gap-3 text-left"
        onClick={() => expandable && setOpen(!open)}
        aria-expanded={expandable ? open : undefined}
      >
        <StatusIcon status={check.status} className="mt-0.5" />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-ink-900">{check.title}</span>
            {check.reference && <Pill>{check.reference}</Pill>}
            <span className="sr-only">{statusLabel(check.status)}</span>
          </div>
          <div className="mt-0.5 text-sm text-ink-500">{check.detail}</div>
        </div>
        {expandable && <ChevronDown className={clsx('mt-1 h-4 w-4 text-ink-400 transition-transform', open && 'rotate-180')} />}
      </button>
      {open && expandable && (
        <div className="mt-3 overflow-x-auto pl-8">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-ink-500">
                {Object.keys(check.rows[0]).map((column) => (
                  <th key={column} className="border-b border-ink-200 px-2 py-1.5 font-medium">
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="tabular-nums">
              {check.rows.map((row, index) => (
                <tr key={index} className="border-b border-ink-100 last:border-0">
                  {Object.values(row).map((value, column) => (
                    <td key={column} className="px-2 py-1.5 text-ink-800">
                      {value}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export function CheckList({ checks }: { checks: Check[] }) {
  return (
    <div className="space-y-4">
      {GROUPS.filter((group) => checks.some((check) => check.group === group.id)).map((group) => {
        const items = checks.filter((check) => check.group === group.id)
        const failed = items.filter((check) => check.status === 'failed').length
        return (
          <Card key={group.id}>
            <CardHeader
              title={group.title}
              subtitle={group.subtitle}
              action={
                <Pill tone={failed ? 'bad' : 'good'}>
                  {items.filter((check) => check.status === 'passed').length} из {items.length}
                </Pill>
              }
            />
            <div className="divide-y divide-ink-100">
              {items.map((check) => (
                <CheckRow key={check.id} check={check} />
              ))}
            </div>
          </Card>
        )
      })}
    </div>
  )
}

function FaultDemo({ issue, meta }: { issue: IssuePackage; meta: Meta }) {
  const [running, setRunning] = useState<string | null>(null)
  const [result, setResult] = useState<FaultResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const run = async (fault: string) => {
    setRunning(fault)
    setError(null)
    try {
      setResult(await api.runFault(issue.id, fault))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Не удалось запустить проверку')
    } finally {
      setRunning(null)
    }
  }

  return (
    <Card className="border-dashed">
      <CardHeader
        title={
          <span className="flex items-center gap-2">
            <FlaskConical className="h-4 w-4 text-brand-700" />
            Что если код поправили вручную?
          </span>
        }
        subtitle="Внесём в контракт типовую ошибку и прогоним те же проверки. Решение о выпуске при этом не меняется"
      />
      <div className="space-y-4 p-5">
        <div className="grid gap-2 md:grid-cols-3">
          {meta.faults.map((fault) => (
            <button
              key={fault.value}
              type="button"
              disabled={running !== null}
              onClick={() => run(fault.value)}
              className={clsx(
                'flex items-start gap-2 rounded-lg border p-3 text-left text-sm transition-colors disabled:opacity-60',
                result?.fault === fault.value ? 'border-brand-600 bg-brand-50' : 'border-ink-200 hover:border-ink-300 hover:bg-ink-50',
              )}
            >
              <Bug className="mt-0.5 h-4 w-4 shrink-0 text-bad" />
              <span className="text-ink-800">{running === fault.value ? 'Проверяем…' : fault.label}</span>
            </button>
          ))}
        </div>
        {error && <ErrorNote>{error}</ErrorNote>}
        {result && (
          <div className="space-y-4">
            <div
              className={clsx(
                'rounded-lg px-4 py-3 text-sm font-medium',
                result.caught ? 'bg-green-50 text-green-900' : 'bg-red-50 text-red-900',
              )}
            >
              {result.caught
                ? `Ошибка поймана. Не пройдено проверок: ${result.failed_checks.length} — ${result.failed_checks.join('; ')}`
                : 'Проверки не заметили изменение'}
            </div>
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-500">Изменения в коде</div>
              <pre className="overflow-x-auto rounded-lg border border-ink-200 bg-ink-50 p-3 font-mono text-xs leading-5">
                {result.diff.map((line, index) => (
                  <div key={index} className={line.startsWith('+') ? 'bg-green-100 text-green-900' : 'bg-red-100 text-red-900'}>
                    {line}
                  </div>
                ))}
              </pre>
            </div>
            <CheckList checks={result.checks.filter((check) => check.group === 'contract')} />
          </div>
        )}
      </div>
    </Card>
  )
}

export function ChecksTab({ issue, meta }: { issue: IssuePackage; meta: Meta }) {
  return (
    <div className="space-y-6">
      <CheckList checks={issue.checks} />
      <FaultDemo issue={issue} meta={meta} />
    </div>
  )
}
