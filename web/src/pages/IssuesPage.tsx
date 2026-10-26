import { useQuery } from '@tanstack/react-query'
import { FilePlus2, FileStack } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '@/api/client'
import { SummaryPills } from '@/components/status'
import { Button, Card, EmptyState, PageHeader, Spinner } from '@/components/ui'
import { amount, date, dateTime, duration, percent } from '@/lib/format'

export function IssuesPage() {
  const navigate = useNavigate()
  const issues = useQuery({ queryKey: ['issues'], queryFn: api.issues })

  return (
    <>
      <PageHeader
        title="Выпуски"
        subtitle="Подготовленные пакеты: решение о выпуске, смарт-контракт и результаты проверок"
        action={
          <Link to="/">
            <Button icon={<FilePlus2 className="h-4 w-4" />}>Новый выпуск</Button>
          </Link>
        }
      />
      {issues.isLoading ? (
        <Spinner />
      ) : !issues.data?.length ? (
        <Card>
          <EmptyState
            icon={<FileStack className="h-6 w-6" />}
            title="Пока нет выпусков"
            text="Опишите первый выпуск обычным языком — пакет документов и проверенный контракт появятся здесь"
            action={
              <Link to="/">
                <Button>Подготовить выпуск</Button>
              </Link>
            }
          />
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-ink-50 text-left text-xs uppercase tracking-wide text-ink-500">
                <tr>
                  <th className="px-5 py-3">Выпуск</th>
                  <th className="px-5 py-3">Эмитент</th>
                  <th className="px-5 py-3 text-right">Объём</th>
                  <th className="px-5 py-3 text-right">Ставка</th>
                  <th className="px-5 py-3">Погашение</th>
                  <th className="px-5 py-3">Подготовка</th>
                  <th className="px-5 py-3">Проверки</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-100">
                {issues.data.map((issue) => (
                  <tr key={issue.id} onClick={() => navigate(`/issues/${issue.id}`)} className="cursor-pointer hover:bg-brand-50/40">
                    <td className="px-5 py-3">
                      <div className="font-medium text-ink-900">{issue.issue_number}</div>
                      <div className="text-xs text-ink-500">{dateTime(issue.created_at)}</div>
                    </td>
                    <td className="px-5 py-3 text-ink-700">{issue.issuer}</td>
                    <td className="px-5 py-3 text-right tabular-nums">{amount(issue.max_amount)}</td>
                    <td className="px-5 py-3 text-right tabular-nums">{percent(issue.coupon_rate)}</td>
                    <td className="px-5 py-3 tabular-nums">{date(issue.maturity_date)}</td>
                    <td className="px-5 py-3 tabular-nums">{duration(issue.preparation_seconds)}</td>
                    <td className="px-5 py-3">
                      <SummaryPills summary={issue.summary} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </>
  )
}
