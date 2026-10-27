import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { IssuePackage } from '@/api/types'
import { Card, CardHeader } from '@/components/ui'
import { date, money } from '@/lib/format'

function ChartTooltip({ active, payload }: { active?: boolean; payload?: { payload: { label: string; coupon: number; days: number; shifted: boolean } }[] }) {
  if (!active || !payload?.length) return null
  const row = payload[0].payload
  return (
    <div className="rounded-lg border border-ink-200 bg-white px-3 py-2 text-xs shadow-lift">
      <div className="font-semibold text-ink-900">{row.label}</div>
      <div className="mt-1 text-ink-700">Доход: {money(row.coupon)} ₽</div>
      <div className="text-ink-500">Дней в периоде: {row.days}</div>
      {row.shifted && <div className="text-ink-500">Перенесено с выходного</div>}
    </div>
  )
}

export function ScheduleTab({ issue }: { issue: IssuePackage }) {
  const data = issue.schedule.map((period) => ({
    label: date(period.payment_date),
    coupon: Number(period.coupon),
    days: period.days,
    shifted: period.shifted,
  }))

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader title="Доход на один ЦФА по датам выплат" subtitle={`Номинал ${money(issue.spec.nominal)} ₽ возвращается в последнюю дату`} />
        <div className="h-64 px-2 py-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
              <CartesianGrid vertical={false} stroke="#eef0f4" />
              <XAxis dataKey="label" tickLine={false} axisLine={{ stroke: '#dde1e8' }} tick={{ fill: '#6b7487', fontSize: 12 }} />
              <YAxis tickLine={false} axisLine={false} tick={{ fill: '#6b7487', fontSize: 12 }} tickFormatter={(value: number) => `${value} ₽`} width={64} />
              <Tooltip content={<ChartTooltip />} cursor={{ fill: '#eff5ff' }} />
              <Bar dataKey="coupon" fill="#2a78d6" radius={[4, 4, 0, 0]} maxBarSize={48} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-ink-50 text-left text-xs uppercase tracking-wide text-ink-500">
              <tr>
                <th className="px-4 py-3">№</th>
                <th className="px-4 py-3">Период начисления</th>
                <th className="px-4 py-3 text-right">Дней</th>
                <th className="px-4 py-3 text-right">Доход, ₽</th>
                <th className="px-4 py-3 text-right">Номинал, ₽</th>
                <th className="px-4 py-3">Дата выплаты</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-100 tabular-nums">
              {issue.schedule.map((period) => (
                <tr key={period.number} className="hover:bg-ink-50/60">
                  <td className="px-4 py-3 text-ink-500">{period.number}</td>
                  <td className="px-4 py-3">
                    {date(period.start)} — {date(period.end)}
                  </td>
                  <td className="px-4 py-3 text-right">{period.days}</td>
                  <td className="px-4 py-3 text-right font-medium">{money(period.coupon)}</td>
                  <td className="px-4 py-3 text-right">{Number(period.principal) ? money(period.principal) : '—'}</td>
                  <td className="px-4 py-3">
                    {date(period.payment_date)}
                    {period.shifted && (
                      <span className="ml-2 rounded bg-amber-50 px-1.5 py-0.5 text-[11px] font-medium text-amber-800">
                        перенос с {date(period.end)}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-ink-50 font-semibold tabular-nums">
              <tr>
                <td className="px-4 py-3" colSpan={3}>
                  Итого на один ЦФА
                </td>
                <td className="px-4 py-3 text-right">{money(issue.totals.coupon)}</td>
                <td className="px-4 py-3 text-right">{money(issue.spec.nominal)}</td>
                <td className="px-4 py-3">{money(issue.totals.payment)} ₽</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </Card>
    </div>
  )
}
