import { useQuery } from '@tanstack/react-query'
import clsx from 'clsx'
import { BarChart3, FilePlus2, FileStack, LayoutTemplate, ShieldCheck, Sparkles } from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'
import { api } from '@/api/client'

const NAV = [
  { to: '/', label: 'Новый выпуск', icon: FilePlus2, end: true },
  { to: '/issues', label: 'Выпуски', icon: FileStack },
  { to: '/templates', label: 'Шаблоны', icon: LayoutTemplate },
  { to: '/metrics', label: 'Метрики', icon: BarChart3 },
  { to: '/platform', label: 'Контур и безопасность', icon: ShieldCheck },
]

export function Layout() {
  const { data: meta } = useQuery({ queryKey: ['meta'], queryFn: api.meta })
  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-ink-200 bg-white lg:flex">
        <div className="flex items-center gap-3 px-5 py-5">
          <img src="/favicon.svg" alt="" className="h-9 w-9" />
          <div>
            <div className="text-[15px] font-semibold text-ink-900">ЦФА Студия</div>
            <div className="text-xs text-ink-500">Подготовка выпуска</div>
          </div>
        </div>
        <nav className="flex flex-col gap-0.5 px-3">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive ? 'bg-brand-50 text-brand-800' : 'text-ink-600 hover:bg-ink-50 hover:text-ink-900',
                )
              }
            >
              <Icon className="h-[18px] w-[18px]" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto border-t border-ink-100 px-5 py-4">
          <div className="flex items-center gap-2 text-xs text-ink-500">
            <Sparkles className="h-3.5 w-3.5 text-brand-600" />
            Разбор описания
          </div>
          <div className="mt-1 text-xs font-medium text-ink-800">{meta?.provider ?? '…'}</div>
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-ink-200 bg-white px-4 py-3 lg:hidden">
          <img src="/favicon.svg" alt="" className="h-7 w-7" />
          <span className="font-semibold">ЦФА Студия</span>
          <nav className="ml-auto flex gap-1">
            {NAV.map(({ to, icon: Icon, label, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                aria-label={label}
                className={({ isActive }) => clsx('rounded-md p-2', isActive ? 'bg-brand-50 text-brand-800' : 'text-ink-500')}
              >
                <Icon className="h-5 w-5" />
              </NavLink>
            ))}
          </nav>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
