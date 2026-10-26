import clsx from 'clsx'
import { CheckCircle2, Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'

const STEPS = [
  'Расчёт графика выплат по производственному календарю',
  'Заполнение решения о выпуске по шаблону',
  'Генерация смарт-контракта',
  'Компиляция Solidity',
  'Сценарии в EVM: сбор заявок, выплаты, погашение',
  'Статический анализ кода',
]

export function BuildingOverlay() {
  const [step, setStep] = useState(0)

  useEffect(() => {
    const timer = window.setInterval(() => setStep((current) => Math.min(current + 1, STEPS.length - 1)), 1400)
    return () => window.clearInterval(timer)
  }, [])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/30 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-lift">
        <div className="text-base font-semibold text-ink-900">Собираем пакет выпуска</div>
        <p className="mt-1 text-sm text-ink-500">Код проверяется исполнением, а не только чтением. Это занимает несколько секунд.</p>
        <ol className="mt-5 space-y-3">
          {STEPS.map((label, index) => (
            <li key={label} className="flex items-center gap-3 text-sm">
              {index < step ? (
                <CheckCircle2 className="h-5 w-5 text-good" />
              ) : index === step ? (
                <Loader2 className="h-5 w-5 animate-spin text-brand-600" />
              ) : (
                <span className="flex h-5 w-5 items-center justify-center">
                  <span className="h-2 w-2 rounded-full bg-ink-200" />
                </span>
              )}
              <span className={clsx(index > step ? 'text-ink-400' : 'text-ink-800')}>{label}</span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  )
}
