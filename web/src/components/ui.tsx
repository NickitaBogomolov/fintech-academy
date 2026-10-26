import clsx from 'clsx'
import { Loader2 } from 'lucide-react'
import type { ButtonHTMLAttributes, ReactNode } from 'react'

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={clsx('rounded-xl border border-ink-200 bg-white shadow-card', className)}>{children}</div>
}

export function CardHeader({ title, subtitle, action }: { title: ReactNode; subtitle?: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-ink-100 px-5 py-4">
      <div>
        <h3 className="text-[15px] font-semibold text-ink-900">{title}</h3>
        {subtitle && <p className="mt-0.5 text-sm text-ink-500">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'

const buttonStyles: Record<ButtonVariant, string> = {
  primary: 'bg-brand-700 text-white hover:bg-brand-800 disabled:bg-ink-300',
  secondary: 'border border-ink-200 bg-white text-ink-800 hover:border-ink-300 hover:bg-ink-50',
  ghost: 'text-ink-600 hover:bg-ink-100 hover:text-ink-900',
  danger: 'border border-red-200 bg-white text-bad hover:bg-red-50',
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  loading?: boolean
  icon?: ReactNode
  size?: 'sm' | 'md' | 'lg'
}

export function Button({
  variant = 'primary',
  loading,
  icon,
  size = 'md',
  className,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 disabled:cursor-not-allowed',
        size === 'sm' && 'h-8 px-3 text-sm',
        size === 'md' && 'h-10 px-4 text-sm',
        size === 'lg' && 'h-12 px-6 text-[15px]',
        buttonStyles[variant],
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
      {children}
    </button>
  )
}

export function LinkButton({
  href,
  icon,
  children,
  variant = 'secondary',
}: {
  href: string
  icon?: ReactNode
  children: ReactNode
  variant?: ButtonVariant
}) {
  return (
    <a
      href={href}
      className={clsx(
        'inline-flex h-9 items-center gap-2 rounded-lg px-3 text-sm font-medium transition-colors',
        buttonStyles[variant],
      )}
    >
      {icon}
      {children}
    </a>
  )
}

export function Stat({ label, value, hint }: { label: string; value: ReactNode; hint?: ReactNode }) {
  return (
    <div className="min-w-0">
      <div className="text-xs font-medium uppercase tracking-wide text-ink-500">{label}</div>
      <div className="mt-1 truncate text-xl font-semibold tabular-nums text-ink-900">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-ink-500">{hint}</div>}
    </div>
  )
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-sm text-ink-500">
      <Loader2 className="h-5 w-5 animate-spin text-brand-600" />
      {label ?? 'Загрузка'}
    </div>
  )
}

export function EmptyState({ icon, title, text, action }: { icon: ReactNode; title: string; text: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center px-6 py-14 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-700">{icon}</div>
      <h3 className="mt-4 text-base font-semibold text-ink-900">{title}</h3>
      <p className="mt-1 max-w-md text-sm text-ink-500">{text}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}

export function PageHeader({ title, subtitle, action }: { title: ReactNode; subtitle?: ReactNode; action?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink-900">{title}</h1>
        {subtitle && <p className="mt-1 max-w-3xl text-sm text-ink-500">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

export function Tabs<T extends string>({
  tabs,
  active,
  onChange,
}: {
  tabs: { id: T; label: string; badge?: ReactNode }[]
  active: T
  onChange: (id: T) => void
}) {
  return (
    <div className="flex gap-1 overflow-x-auto border-b border-ink-200">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={clsx(
            '-mb-px flex shrink-0 items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors',
            tab.id === active
              ? 'border-brand-700 text-brand-800'
              : 'border-transparent text-ink-500 hover:border-ink-300 hover:text-ink-800',
          )}
        >
          {tab.label}
          {tab.badge}
        </button>
      ))}
    </div>
  )
}

export function Pill({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'brand' | 'good' | 'warn' | 'bad' }) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
        tone === 'neutral' && 'bg-ink-100 text-ink-700',
        tone === 'brand' && 'bg-brand-50 text-brand-800',
        tone === 'good' && 'bg-green-50 text-green-800',
        tone === 'warn' && 'bg-amber-50 text-amber-800',
        tone === 'bad' && 'bg-red-50 text-red-700',
      )}
    >
      {children}
    </span>
  )
}

export function ErrorNote({ children }: { children: ReactNode }) {
  return <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{children}</div>
}
