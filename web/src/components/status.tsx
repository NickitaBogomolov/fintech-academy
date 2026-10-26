import clsx from 'clsx'
import { AlertTriangle, CheckCircle2, MinusCircle, XCircle } from 'lucide-react'
import type { CheckStatus, Origin, Summary } from '@/api/types'
import { Pill } from './ui'

const STATUS = {
  passed: { icon: CheckCircle2, label: 'Пройдена', className: 'text-good' },
  warning: { icon: AlertTriangle, label: 'Замечание', className: 'text-warn' },
  failed: { icon: XCircle, label: 'Не пройдена', className: 'text-bad' },
  skipped: { icon: MinusCircle, label: 'Не запускалась', className: 'text-ink-400' },
} as const

export function StatusIcon({ status, className }: { status: CheckStatus; className?: string }) {
  const { icon: Icon, label, className: color } = STATUS[status]
  return <Icon aria-label={label} className={clsx('h-5 w-5 shrink-0', color, className)} />
}

export function statusLabel(status: CheckStatus): string {
  return STATUS[status].label
}

export function SummaryPills({ summary }: { summary: Summary }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      <Pill tone="good">
        <CheckCircle2 className="h-3.5 w-3.5" />
        {summary.passed}
      </Pill>
      {summary.warning > 0 && (
        <Pill tone="warn">
          <AlertTriangle className="h-3.5 w-3.5" />
          {summary.warning}
        </Pill>
      )}
      {summary.failed > 0 && (
        <Pill tone="bad">
          <XCircle className="h-3.5 w-3.5" />
          {summary.failed}
        </Pill>
      )}
    </div>
  )
}

const ORIGIN: Record<Origin, { label: string; className: string }> = {
  text: { label: 'из описания', className: 'bg-brand-50 text-brand-800 ring-brand-200' },
  answer: { label: 'уточнено', className: 'bg-green-50 text-green-800 ring-green-200' },
  default: { label: 'по умолчанию', className: 'bg-ink-100 text-ink-600 ring-ink-200' },
  registry: { label: 'из реестра', className: 'bg-violet-50 text-violet-800 ring-violet-200' },
}

export function OriginChip({ origin }: { origin: Origin }) {
  const { label, className } = ORIGIN[origin]
  return <span className={clsx('rounded-md px-1.5 py-0.5 text-[11px] font-medium ring-1 ring-inset', className)}>{label}</span>
}
