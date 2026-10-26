import { useQuery } from '@tanstack/react-query'
import { CheckCircle2, Clock3, Download, FileCode2, FileJson, FileText, TriangleAlert } from 'lucide-react'
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '@/api/client'
import type { IssuePackage, Meta } from '@/api/types'
import { CodeView } from '@/components/CodeView'
import { Markdown } from '@/components/Markdown'
import { OriginChip, SummaryPills } from '@/components/status'
import { Card, CardHeader, ErrorNote, LinkButton, Pill, Spinner, Stat, Tabs } from '@/components/ui'
import { FREQUENCY, amount, date, dateTime, duration, integer, money, percent } from '@/lib/format'
import { displayValue } from '../new/FieldInput'
import { ChecksTab } from './ChecksTab'
import { InvestorTab } from './InvestorTab'
import { ScheduleTab } from './ScheduleTab'

type TabId = 'document' | 'schedule' | 'contract' | 'checks' | 'investor' | 'source'

function Verdict({ issue }: { issue: IssuePackage }) {
  const { failed, warning } = issue.summary
  if (failed) {
    return (
      <div className="flex items-center gap-2 rounded-lg bg-red-50 px-3 py-2 text-sm font-medium text-red-800">
        <TriangleAlert className="h-4 w-4" />
        Есть непройденные проверки: пакет нельзя отправлять оператору
      </div>
    )
  }
  return (
    <div className="flex items-center gap-2 rounded-lg bg-green-50 px-3 py-2 text-sm font-medium text-green-900">
      <CheckCircle2 className="h-4 w-4" />
      {warning ? `Готов к проверке юристом, замечаний: ${warning}` : 'Готов к проверке юристом'}
    </div>
  )
}

function SourceTab({ issue, meta }: { issue: IssuePackage; meta: Meta }) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader title="Исходное описание" subtitle={`Разбор: ${issue.provider}`} />
        <p className="whitespace-pre-wrap px-5 py-4 text-sm leading-7 text-ink-700">{issue.text}</p>
      </Card>
      <Card>
        <CardHeader title="Откуда взялся каждый параметр" />
        <div className="divide-y divide-ink-100">
          {meta.fields.map((field) => {
            const item = issue.values[field.key]
            return (
              <div key={field.key} className="flex items-center justify-between gap-3 px-5 py-2.5 text-sm">
                <span className="text-ink-600">{field.label}</span>
                <span className="flex items-center gap-2">
                  <span className="font-medium tabular-nums text-ink-900">{displayValue(field.kind, item?.value, field.choices)}</span>
                  {item && <OriginChip origin={item.origin} />}
                </span>
              </div>
            )
          })}
        </div>
      </Card>
    </div>
  )
}

export function IssuePage() {
  const { id = '' } = useParams()
  const [tab, setTab] = useState<TabId>('document')
  const issue = useQuery({ queryKey: ['issue', id], queryFn: () => api.issue(id) })
  const meta = useQuery({ queryKey: ['meta'], queryFn: api.meta })

  if (issue.isLoading || meta.isLoading) return <Spinner />
  if (!issue.data || !meta.data) return <ErrorNote>Выпуск не найден</ErrorNote>
  const data = issue.data
  const { spec } = data
  const failedChecks = data.summary.failed

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight text-ink-900">Выпуск {spec.issue_number}</h1>
            <Pill tone="brand">{data.template.title}</Pill>
          </div>
          <p className="mt-1 text-sm text-ink-500">
            {spec.issuer.short_name} · ИНН {spec.issuer.inn} · подготовлен {dateTime(data.created_at)}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <LinkButton href={api.fileUrl(data.id, 'decision.docx')} icon={<FileText className="h-4 w-4" />} variant="primary">
            Решение, DOCX
          </LinkButton>
          <LinkButton href={api.fileUrl(data.id, 'contract.sol')} icon={<FileCode2 className="h-4 w-4" />}>
            Контракт
          </LinkButton>
          <LinkButton href={api.fileUrl(data.id, 'package.json')} icon={<FileJson className="h-4 w-4" />}>
            Пакет
          </LinkButton>
        </div>
      </div>

      <Card className="p-5">
        <div className="grid grid-cols-2 gap-5 md:grid-cols-3 lg:grid-cols-6">
          <Stat label="Объём" value={amount(spec.max_amount)} hint={`от ${amount(spec.min_amount)}`} />
          <Stat label="Ставка" value={percent(spec.coupon_rate)} hint={FREQUENCY[spec.coupon_frequency]} />
          <Stat label="Срок" value={`${spec.term_days} дн.`} hint={`${date(spec.issue_date)} — ${date(spec.maturity_date)}`} />
          <Stat label="Доход на 1 ЦФА" value={`${money(data.totals.coupon)} ₽`} hint={`номинал ${money(spec.nominal)} ₽`} />
          <Stat label="ЦФА в выпуске" value={integer(spec.max_quantity)} hint={`минимум ${integer(spec.min_quantity)}`} />
          <Stat
            label="Подготовка"
            value={
              <span className="flex items-center gap-1.5">
                <Clock3 className="h-4 w-4 text-ink-400" />
                {duration(data.metrics.preparation_seconds)}
              </span>
            }
            hint={`вопросов: ${data.metrics.questions_asked}`}
          />
        </div>
        <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-ink-100 pt-4">
          <Verdict issue={data} />
          <button type="button" onClick={() => setTab('checks')} className="flex items-center gap-2 text-sm text-ink-600 hover:text-ink-900">
            Проверки
            <SummaryPills summary={data.summary} />
          </button>
        </div>
      </Card>

      <Tabs<TabId>
        active={tab}
        onChange={setTab}
        tabs={[
          { id: 'document', label: 'Решение о выпуске' },
          { id: 'schedule', label: 'График выплат' },
          { id: 'contract', label: 'Смарт-контракт' },
          {
            id: 'checks',
            label: 'Проверки',
            badge: <Pill tone={failedChecks ? 'bad' : 'good'}>{data.checks.length}</Pill>,
          },
          { id: 'investor', label: 'Карточка инвестора' },
          { id: 'source', label: 'Исходные данные' },
        ]}
      />

      {tab === 'document' && (
        <Card className="px-6 py-10 sm:px-12">
          <Markdown>{data.document}</Markdown>
        </Card>
      )}
      {tab === 'schedule' && <ScheduleTab issue={data} />}
      {tab === 'contract' && (
        <Card>
          <CardHeader
            title={`${data.contract.name}.sol`}
            subtitle={`Константы выпуска подставлены из спецификации · ${data.compiler ? `solc ${data.compiler.split('+')[0]}` : 'компилятор не запускался'}`}
            action={
              <LinkButton href={api.fileUrl(data.id, 'contract.sol')} icon={<Download className="h-4 w-4" />}>
                Скачать
              </LinkButton>
            }
          />
          <div className="p-4">
            <CodeView code={data.contract.source} language="solidity" />
          </div>
        </Card>
      )}
      {tab === 'checks' && <ChecksTab issue={data} meta={meta.data} />}
      {tab === 'investor' && <InvestorTab issue={data} />}
      {tab === 'source' && <SourceTab issue={data} meta={meta.data} />}
    </div>
  )
}
