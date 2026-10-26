import { ArrowRight, FileCode2, FileText, ListChecks, Sparkles, UserRound, WalletCards } from 'lucide-react'
import type { Meta } from '@/api/types'
import { Button, Card } from '@/components/ui'

interface Props {
  meta: Meta
  text: string
  inn: string
  loading: boolean
  onText: (text: string) => void
  onInn: (inn: string) => void
  onSubmit: () => void
}

const OUTPUTS = [
  { icon: FileText, title: 'Решение о выпуске', text: 'по шаблону оператора, DOCX' },
  { icon: WalletCards, title: 'График выплат', text: 'с учётом выходных и праздников' },
  { icon: FileCode2, title: 'Смарт-контракт', text: 'Solidity, параметры из той же спецификации' },
  { icon: ListChecks, title: 'Проверки', text: 'арифметика, календарь, регуляторика, исполнение в EVM' },
  { icon: UserRound, title: 'Карточка инвестора', text: 'условия простым языком' },
]

export function DescribeStep({ meta, text, inn, loading, onText, onInn, onSubmit }: Props) {
  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      <Card className="p-6">
        <label htmlFor="description" className="text-[15px] font-semibold text-ink-900">
          Опишите выпуск своими словами
        </label>
        <p className="mt-1 text-sm text-ink-500">
          Сколько нужно привлечь, на какой срок, под какую ставку и для кого. Недостающее система спросит сама.
        </p>
        <textarea
          id="description"
          value={text}
          onChange={(event) => onText(event.target.value)}
          rows={7}
          placeholder="Например: хотим привлечь до 300 млн рублей на полгода, номинал 1000 ₽, купон 18% годовых ежемесячно, только для квалифицированных инвесторов"
          className="mt-4 w-full resize-y rounded-xl border border-ink-200 bg-white p-4 text-[15px] leading-relaxed outline-none transition placeholder:text-ink-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-100"
        />
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-ink-500">Примеры:</span>
          {meta.examples.map((example) => (
            <button
              key={example.title}
              type="button"
              onClick={() => {
                onText(example.text)
                onInn(example.inn)
              }}
              className="rounded-full border border-ink-200 bg-white px-3 py-1 text-xs font-medium text-ink-700 transition hover:border-brand-300 hover:bg-brand-50 hover:text-brand-800"
            >
              {example.title}
            </button>
          ))}
        </div>

        <div className="mt-6 grid gap-4 border-t border-ink-100 pt-5 sm:grid-cols-[1fr_auto] sm:items-end">
          <div>
            <label htmlFor="issuer" className="text-sm font-medium text-ink-800">
              Эмитент
            </label>
            <select id="issuer" value={inn} onChange={(event) => onInn(event.target.value)} className="field-input mt-1.5">
              <option value="">Указать позже или по ИНН в тексте</option>
              {meta.issuers.map((issuer) => (
                <option key={issuer.inn} value={issuer.inn}>
                  {issuer.short_name} · ИНН {issuer.inn}
                </option>
              ))}
            </select>
            <p className="mt-1.5 text-xs text-ink-500">Реквизиты подтягиваются из реестра юридических лиц</p>
          </div>
          <Button
            size="lg"
            onClick={onSubmit}
            loading={loading}
            disabled={text.trim().length < 10}
            icon={<Sparkles className="h-4 w-4" />}
          >
            Разобрать описание
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </Card>

      <Card className="h-fit p-5">
        <div className="text-xs font-semibold uppercase tracking-wide text-ink-500">Пакет выпуска</div>
        <p className="mt-1 text-sm text-ink-600">Всё собирается из одной спецификации, поэтому документ и код не расходятся.</p>
        <ul className="mt-4 space-y-3">
          {OUTPUTS.map(({ icon: Icon, title, text: caption }) => (
            <li key={title} className="flex gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
                <Icon className="h-4 w-4" />
              </div>
              <div>
                <div className="text-sm font-medium text-ink-900">{title}</div>
                <div className="text-xs text-ink-500">{caption}</div>
              </div>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  )
}
