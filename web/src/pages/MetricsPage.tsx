import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Gauge, Play } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '@/api/client'
import type { Benchmark, Metrics } from '@/api/types'
import { Button, Card, CardHeader, EmptyState, PageHeader, Spinner, Stat } from '@/components/ui'
import { dateTime, duration } from '@/lib/format'

const PILOT_METRICS = [
  {
    metric: 'Время от обращения эмитента до пакета, готового к проверке юристом',
    how: 'Отметки времени в журнале выпуска против текущего процесса оператора',
    target: 'Сократить в разы; базу фиксируем на интервью и первых выпусках пилота',
  },
  {
    metric: 'Итерации правок решения о выпуске между эмитентом, юристом и оператором',
    how: 'Количество версий документа до подписания',
    target: 'Не больше одной итерации на типовой выпуск',
  },
  {
    metric: 'Расхождения документа и смарт-контракта, найденные до размещения',
    how: 'Непройденные проверки исполнения в EVM',
    target: 'Ноль расхождений в размещённых выпусках',
  },
  {
    metric: 'Доля параметров, извлечённых из описания без правок',
    how: 'Происхождение каждого поля в пакете выпуска',
    target: 'Не ниже 60% на описаниях реальных эмитентов',
  },
  {
    metric: 'Выпусков на одного сотрудника оператора в месяц',
    how: 'Выпуски в системе / сотрудники команды ЦФА',
    target: 'Рост без расширения команды',
  },
]

function share(part: number | undefined, total: number | undefined): string {
  if (!part || !total) return '—'
  return `${Math.round((part / total) * 100)}%`
}

function KpiGrid({ metrics }: { metrics: Metrics }) {
  const checksTotal = Object.values(metrics.checks).reduce((sum, value) => sum + (value ?? 0), 0)
  return (
    <Card className="p-5">
      <div className="grid grid-cols-2 gap-6 md:grid-cols-3 lg:grid-cols-6">
        <Stat label="Выпусков" value={metrics.issues} hint="подготовлено в системе" />
        <Stat label="Медиана подготовки" value={duration(metrics.median_preparation_seconds)} hint="от описания до пакета" />
        <Stat label="Из описания" value={share(metrics.fields.from_text, metrics.fields.fields_total)} hint="параметров без ручного ввода" />
        <Stat label="Вопросов" value={metrics.avg_questions ?? '—'} hint="в среднем на выпуск" />
        <Stat label="Проверок пройдено" value={share(metrics.checks.passed, checksTotal)} hint={`всего ${checksTotal}`} />
        <Stat
          label="Ошибок поймано"
          value={metrics.fault_runs ? `${metrics.faults_caught} из ${metrics.fault_runs}` : '—'}
          hint="внесённых в код вручную"
        />
      </div>
    </Card>
  )
}

function PreparationChart({ metrics }: { metrics: Metrics }) {
  const data = metrics.timeline
    .filter((item) => item.preparation_seconds != null)
    .map((item) => ({ name: item.issue_number, minutes: Number(((item.preparation_seconds ?? 0) / 60).toFixed(1)), when: item.created_at }))
  return (
    <Card>
      <CardHeader title="Время подготовки выпуска" subtitle="Минуты от начала описания до готового пакета" />
      <div className="h-64 px-2 py-4">
        {data.length ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
              <CartesianGrid vertical={false} stroke="#eef0f4" />
              <XAxis dataKey="name" tickLine={false} axisLine={{ stroke: '#dde1e8' }} tick={{ fill: '#6b7487', fontSize: 11 }} />
              <YAxis tickLine={false} axisLine={false} tick={{ fill: '#6b7487', fontSize: 12 }} width={40} />
              <Tooltip
                cursor={{ fill: '#eff5ff' }}
                formatter={(value: number) => [`${value} мин`, 'Подготовка']}
                labelFormatter={(label: string, payload) => `${label} · ${payload?.[0] ? dateTime(payload[0].payload.when) : ''}`}
              />
              <Bar dataKey="minutes" fill="#2a78d6" radius={[4, 4, 0, 0]} maxBarSize={40} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-ink-500">Появится после первого выпуска</div>
        )}
      </div>
    </Card>
  )
}

function OriginsCard({ metrics }: { metrics: Metrics }) {
  const total = metrics.fields.fields_total ?? 0
  const rows = [
    { label: 'Из описания', value: metrics.fields.from_text ?? 0, color: 'bg-series-1' },
    { label: 'Уточнено вопросами', value: metrics.fields.from_answers ?? 0, color: 'bg-green-600' },
    { label: 'По умолчанию', value: metrics.fields.from_defaults ?? 0, color: 'bg-ink-300' },
  ]
  return (
    <Card>
      <CardHeader title="Откуда берутся параметры" subtitle="Сколько пользователь вводит руками" />
      <div className="space-y-4 p-5">
        <div className="flex h-3 gap-0.5 overflow-hidden rounded-full bg-ink-100">
          {rows.map((row) => (
            <div key={row.label} className={row.color} style={{ width: total ? `${(row.value / total) * 100}%` : 0 }} />
          ))}
        </div>
        <dl className="space-y-2 text-sm">
          {rows.map((row) => (
            <div key={row.label} className="flex items-center justify-between">
              <dt className="flex items-center gap-2 text-ink-600">
                <i className={`h-2.5 w-2.5 rounded-full ${row.color}`} />
                {row.label}
              </dt>
              <dd className="font-medium tabular-nums text-ink-900">
                {row.value} <span className="text-ink-400">· {share(row.value, total)}</span>
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </Card>
  )
}

function BenchmarkCard({ benchmark }: { benchmark: Benchmark | null }) {
  const queryClient = useQueryClient()
  const run = useMutation({
    mutationFn: api.runBenchmark,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['metrics'] }),
  })
  return (
    <Card>
      <CardHeader
        title="Качество разбора описаний"
        subtitle={benchmark ? `${benchmark.dataset} · ${benchmark.provider} · ${dateTime(benchmark.created_at)}` : 'Эталонный набор описаний с известными параметрами'}
        action={
          <Button size="sm" variant="secondary" icon={<Play className="h-3.5 w-3.5" />} loading={run.isPending} onClick={() => run.mutate()}>
            Запустить
          </Button>
        }
      />
      {benchmark ? (
        <div className="space-y-5 p-5">
          <div className="grid grid-cols-3 gap-4">
            <Stat label="Полнота" value={`${Math.round(benchmark.recall * 100)}%`} hint={`${benchmark.fields_correct} из ${benchmark.fields_expected} полей`} />
            <Stat label="Точность" value={`${Math.round(benchmark.precision * 100)}%`} hint="без ложных значений" />
            <Stat label="Без ошибок" value={`${benchmark.exact_cases} из ${benchmark.cases}`} hint="описаний целиком" />
          </div>
          <div className="space-y-2">
            {benchmark.per_field.map((field) => {
              const value = field.correct / field.expected
              return (
                <div key={field.key} className="grid grid-cols-[200px_1fr_56px] items-center gap-3 text-sm">
                  <span className="truncate text-ink-600" title={field.label}>
                    {field.label}
                  </span>
                  <div className="h-2 rounded-full bg-ink-100">
                    <div className="h-2 rounded-full bg-series-1" style={{ width: `${value * 100}%` }} />
                  </div>
                  <span className="text-right tabular-nums text-ink-700">
                    {field.correct}/{field.expected}
                  </span>
                </div>
              )
            })}
          </div>
          {benchmark.failures.length > 0 && (
            <details className="rounded-lg border border-ink-200 p-3 text-sm">
              <summary className="cursor-pointer font-medium text-ink-800">Где разбор ошибается ({benchmark.failures.length})</summary>
              <ul className="mt-3 space-y-3">
                {benchmark.failures.map((failure) => (
                  <li key={failure.text}>
                    <p className="text-ink-700">«{failure.text}»</p>
                    <ul className="mt-1 space-y-0.5 text-xs text-ink-500">
                      {failure.errors.map((error) => (
                        <li key={error.field}>
                          {error.field}: ожидалось {error.expected ?? '—'}, получено {error.actual ?? 'ничего'}
                        </li>
                      ))}
                    </ul>
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-xs text-ink-500">
                Числа словами и условные формулировки — задача для языковой модели: подключается через настройку DFA_LLM_PROVIDER.
              </p>
            </details>
          )}
          <p className="text-xs text-ink-500">{benchmark.source}</p>
        </div>
      ) : (
        <EmptyState icon={<Gauge className="h-6 w-6" />} title="Замер ещё не запускался" text="Запустите, чтобы получить полноту и точность извлечения параметров" />
      )}
    </Card>
  )
}

export function MetricsPage() {
  const metrics = useQuery({ queryKey: ['metrics'], queryFn: api.metrics })
  if (metrics.isLoading || !metrics.data) return <Spinner />
  const data = metrics.data
  return (
    <div className="space-y-6">
      <PageHeader title="Продуктовые метрики" subtitle="Что измеряется уже сейчас и что будем подтверждать на пилоте" />
      <KpiGrid metrics={data} />
      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <PreparationChart metrics={data} />
        <OriginsCard metrics={data} />
      </div>
      <BenchmarkCard benchmark={data.benchmark} />
      <Card className="overflow-hidden">
        <CardHeader title="Метрики пилота" subtitle="Как будем измерять эффект в контуре оператора" />
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-ink-50 text-left text-xs uppercase tracking-wide text-ink-500">
              <tr>
                <th className="px-5 py-3">Метрика</th>
                <th className="px-5 py-3">Как измеряем</th>
                <th className="px-5 py-3">Цель</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-100">
              {PILOT_METRICS.map((row) => (
                <tr key={row.metric}>
                  <td className="px-5 py-3 font-medium text-ink-900">{row.metric}</td>
                  <td className="px-5 py-3 text-ink-600">{row.how}</td>
                  <td className="px-5 py-3 text-ink-600">{row.target}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
