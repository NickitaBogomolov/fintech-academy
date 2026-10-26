import { CalendarDays, Coins, Lock, ShieldAlert } from 'lucide-react'
import type { IssuePackage } from '@/api/types'
import { Card } from '@/components/ui'
import { FREQUENCY, INVESTORS, date, money, percent } from '@/lib/format'

export function InvestorTab({ issue }: { issue: IssuePackage }) {
  const { spec, totals } = issue
  const invested = Number(spec.price)
  const returned = Number(totals.payment)
  const firstPayment = issue.schedule[0]

  return (
    <div className="mx-auto max-w-3xl">
      <Card className="overflow-hidden">
        <div className="bg-gradient-to-br from-brand-800 to-brand-600 px-6 py-6 text-white">
          <div className="text-sm text-brand-100">Цифровой финансовый актив · {spec.issue_number}</div>
          <div className="mt-1 text-xl font-semibold">{spec.issuer.short_name}</div>
          <div className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <div className="text-xs text-brand-100">Ставка</div>
              <div className="text-2xl font-semibold tabular-nums">{percent(spec.coupon_rate)}</div>
            </div>
            <div>
              <div className="text-xs text-brand-100">Выплаты</div>
              <div className="text-lg font-semibold">{FREQUENCY[spec.coupon_frequency]}</div>
            </div>
            <div>
              <div className="text-xs text-brand-100">Погашение</div>
              <div className="text-lg font-semibold tabular-nums">{date(spec.maturity_date)}</div>
            </div>
            <div>
              <div className="text-xs text-brand-100">Цена 1 ЦФА</div>
              <div className="text-lg font-semibold tabular-nums">{money(spec.price)} ₽</div>
            </div>
          </div>
        </div>

        <div className="space-y-6 p-6">
          <section>
            <h3 className="flex items-center gap-2 text-sm font-semibold text-ink-900">
              <Coins className="h-4 w-4 text-brand-700" />
              Что вы получите на один ЦФА
            </h3>
            <div className="mt-3 space-y-2">
              {[
                { label: 'Вложите', value: invested, tone: 'bg-ink-300' },
                { label: 'Получите за весь срок', value: returned, tone: 'bg-series-1' },
              ].map((row) => (
                <div key={row.label} className="grid grid-cols-[150px_1fr_110px] items-center gap-3 text-sm">
                  <span className="text-ink-600">{row.label}</span>
                  <div className="h-3 rounded-r bg-ink-100">
                    <div className={`h-3 rounded-r ${row.tone}`} style={{ width: `${(row.value / returned) * 100}%` }} />
                  </div>
                  <span className="text-right font-medium tabular-nums">{money(row.value)} ₽</span>
                </div>
              ))}
            </div>
            <p className="mt-3 text-sm text-ink-600">
              Доход {money(totals.coupon)} ₽ — это {percent(totals.simple_yield)} годовых без учёта реинвестирования и налогов.
            </p>
          </section>

          <section>
            <h3 className="flex items-center gap-2 text-sm font-semibold text-ink-900">
              <CalendarDays className="h-4 w-4 text-brand-700" />
              Как приходят деньги
            </h3>
            <p className="mt-2 text-sm text-ink-600">
              Первая выплата {firstPayment ? `${date(firstPayment.payment_date)} — ${money(firstPayment.coupon)} ₽` : '—'}. Всего выплат:{' '}
              {issue.schedule.length}. Если дата выпадает на выходной, выплата переносится по правилам решения о выпуске. Деньги
              приходят автоматически: их распределяет смарт-контракт.
            </p>
          </section>

          <section>
            <h3 className="flex items-center gap-2 text-sm font-semibold text-ink-900">
              <ShieldAlert className="h-4 w-4 text-brand-700" />
              Риски
            </h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-ink-600">
              <li>Если эмитент не сможет заплатить, вы можете получить меньше или с задержкой: выпуск не обеспечен.</li>
              <li>Продать ЦФА до погашения может быть невозможно или только со скидкой.</li>
              <li>ЦФА не застрахованы в системе страхования вкладов.</li>
              <li>Кредитный рейтинг эмитента: {spec.issuer.rating ?? 'отсутствует'}.</li>
            </ul>
          </section>

          <section className="flex items-start gap-2 rounded-lg bg-ink-50 p-4 text-sm text-ink-700">
            <Lock className="mt-0.5 h-4 w-4 shrink-0 text-ink-500" />
            <span>
              {INVESTORS[spec.investors]}. Покупка возможна только после идентификации у оператора. Карточка сформирована из тех же
              параметров, что решение о выпуске и смарт-контракт.
            </span>
          </section>
        </div>
      </Card>
    </div>
  )
}
