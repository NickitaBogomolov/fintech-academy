import { useQuery } from '@tanstack/react-query'
import clsx from 'clsx'
import { Boxes, Cpu, Database, FileCheck2, KeyRound, Network, ServerCog, ShieldCheck } from 'lucide-react'
import type { ReactNode } from 'react'
import { api } from '@/api/client'
import { Card, CardHeader, PageHeader, Pill, Spinner } from '@/components/ui'

const COMPLIANCE = [
  {
    norm: '152-ФЗ',
    how: 'В модель уходит только текст условий выпуска. Персональные данные инвесторов система не обрабатывает, реквизиты эмитента берутся из реестра юрлиц',
  },
  {
    norm: '115-ФЗ',
    how: 'Смарт-контракт принимает заявки и переводы только от лиц, отмеченных оператором как идентифицированные; квалификация проверяется там же',
  },
  {
    norm: '259-ФЗ',
    how: 'Решение о выпуске собирается по шаблону оператора, обязательства зафиксированы константами и не меняются после выпуска',
  },
  {
    norm: 'Требования ИБ',
    how: 'Ключи подписи не попадают в систему: контракт разворачивает оператор своими средствами. Сгенерированный код исполняется только в изолированной EVM',
  },
  {
    norm: 'Импортозамещение',
    how: 'Открытый код без зарубежных облаков. Модели: GigaChat, YandexGPT или открытые модели в контуре; СУБД — PostgreSQL / Postgres Pro',
  },
]

const SCALING = [
  'Сервис без состояния: горизонтально масштабируется за балансировщиком',
  'Проверка контракта — изолированная задача: на пилоте выносится в очередь и отдельные воркеры',
  'Хранилище SQLite в демо заменяется на PostgreSQL без изменения API',
  'Модель подключается по OpenAI-совместимому протоколу: vLLM, GigaChat, YandexGPT',
  'Новые типы инструментов добавляются шаблоном документа и шаблоном контракта',
]

function Box({ icon, title, text, tone = 'neutral' }: { icon: ReactNode; title: string; text: string; tone?: 'neutral' | 'brand' }) {
  return (
    <div className={clsx('rounded-xl border p-4', tone === 'brand' ? 'border-brand-200 bg-brand-50/60' : 'border-ink-200 bg-white')}>
      <div className="flex items-center gap-2 text-sm font-semibold text-ink-900">
        {icon}
        {title}
      </div>
      <div className="mt-1 text-xs text-ink-600">{text}</div>
    </div>
  )
}

export function PlatformPage() {
  const system = useQuery({ queryKey: ['system'], queryFn: api.system })
  if (system.isLoading || !system.data) return <Spinner />
  const info = system.data
  const offline = info.external_hosts.length === 0

  return (
    <div className="space-y-6">
      <PageHeader
        title="Контур и безопасность"
        subtitle="Решение разворачивается целиком внутри контура оператора и работает без доступа в интернет"
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="p-5">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-ink-500">
            <Cpu className="h-4 w-4" />
            Разбор описаний
          </div>
          <div className="mt-2 text-base font-semibold text-ink-900">{info.llm.label}</div>
          <div className="mt-1 text-sm text-ink-500">{info.llm.model ? `${info.llm.model} · ${info.llm.endpoint}` : 'Правила на сервере, модель не требуется'}</div>
        </Card>
        <Card className="p-5">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-ink-500">
            <Network className="h-4 w-4" />
            Внешние вызовы
          </div>
          <div className="mt-2 text-base font-semibold text-ink-900">{offline ? 'Нет' : info.external_hosts.join(', ')}</div>
          <div className="mt-1 text-sm text-ink-500">{offline ? 'Все вычисления внутри сервиса' : 'Только адрес модели внутри контура'}</div>
        </Card>
        <Card className="p-5">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-ink-500">
            <FileCheck2 className="h-4 w-4" />
            Проверка кода
          </div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <Pill tone={info.toolchain.solc ? 'good' : 'warn'}>solc {info.toolchain.solc?.split('+')[0] ?? 'не установлен'}</Pill>
            <Pill tone="good">EVM</Pill>
            <Pill tone={info.toolchain.slither ? 'good' : 'warn'}>Slither {info.toolchain.slither ? '' : 'не установлен'}</Pill>
          </div>
          <div className="mt-2 text-sm text-ink-500">{info.toolchain.evm}</div>
        </Card>
      </div>

      <Card>
        <CardHeader title="Архитектура в контуре оператора" subtitle="Что где работает и какие данные куда идут" />
        <div className="grid gap-4 p-5 lg:grid-cols-[1fr_auto_1.4fr_auto_1fr] lg:items-center">
          <div className="space-y-3">
            <Box icon={<Boxes className="h-4 w-4 text-brand-700" />} title="Веб-интерфейс" text="Сотрудник оператора или менеджер эмитента" />
            <Box icon={<FileCheck2 className="h-4 w-4 text-brand-700" />} title="Шаблоны оператора" text="Формы решений о выпуске и контрактов" />
          </div>
          <div className="hidden text-center text-ink-300 lg:block">→</div>
          <div className="rounded-2xl border-2 border-dashed border-brand-200 p-4">
            <div className="mb-3 text-center text-xs font-semibold uppercase tracking-wide text-brand-800">ЦФА Студия</div>
            <div className="grid gap-3 sm:grid-cols-2">
              <Box tone="brand" icon={<Cpu className="h-4 w-4 text-brand-700" />} title="Разбор описания" text="Правила или модель в контуре" />
              <Box tone="brand" icon={<ServerCog className="h-4 w-4 text-brand-700" />} title="Спецификация" text="Единый источник параметров" />
              <Box tone="brand" icon={<FileCheck2 className="h-4 w-4 text-brand-700" />} title="Документ и контракт" text="Генерация по шаблонам" />
              <Box tone="brand" icon={<ShieldCheck className="h-4 w-4 text-brand-700" />} title="Верификация" text="solc, EVM, Slither" />
            </div>
          </div>
          <div className="hidden text-center text-ink-300 lg:block">→</div>
          <div className="space-y-3">
            <Box icon={<Database className="h-4 w-4 text-brand-700" />} title="Хранилище" text={info.storage} />
            <Box icon={<KeyRound className="h-4 w-4 text-brand-700" />} title="Платформа ОИС" text="Развёртывание и подпись — средствами оператора" />
          </div>
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Соответствие требованиям" />
          <div className="divide-y divide-ink-100">
            {COMPLIANCE.map((row) => (
              <div key={row.norm} className="grid gap-2 px-5 py-3 sm:grid-cols-[170px_1fr]">
                <div className="text-sm font-semibold text-ink-900">{row.norm}</div>
                <div className="text-sm text-ink-600">{row.how}</div>
              </div>
            ))}
          </div>
        </Card>
        <Card>
          <CardHeader title="Масштабирование" />
          <ul className="space-y-3 px-5 py-4">
            {SCALING.map((item) => (
              <li key={item} className="flex gap-3 text-sm text-ink-700">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-600" />
                {item}
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  )
}
