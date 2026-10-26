import type {
  Benchmark,
  Draft,
  FaultResult,
  IssueListItem,
  IssuePackage,
  Meta,
  Metrics,
  SystemInfo,
  TemplateInfo,
  Values,
} from './types'

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly fields: Record<string, string> = {},
  ) {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const detail = typeof body.detail === 'string' ? body.detail : 'Не удалось выполнить запрос'
    throw new ApiError(detail, response.status, body.fields ?? {})
  }
  return response.json() as Promise<T>
}

const post = <T>(path: string, body: unknown) => request<T>(path, { method: 'POST', body: JSON.stringify(body) })

export const api = {
  meta: () => request<Meta>('/meta'),
  system: () => request<SystemInfo>('/system'),
  draft: (text: string, inn?: string) => post<Draft>('/drafts', { text, inn: inn || null }),
  createIssue: (payload: {
    text: string
    values: Values
    template_id: string
    started_at: string
    questions_asked: number
  }) => post<IssuePackage>('/issues', payload),
  issues: () => request<IssueListItem[]>('/issues'),
  issue: (id: string) => request<IssuePackage>(`/issues/${id}`),
  runFault: (id: string, fault: string) => post<FaultResult>(`/issues/${id}/faults`, { fault }),
  fileUrl: (id: string, name: string) => `/api/issues/${id}/files/${name}`,
  templates: () => request<TemplateInfo[]>('/templates'),
  previewTemplate: (source: string) => post<{ document: string }>('/templates/preview', { source }),
  saveTemplate: (id: string, source: string) => post<TemplateInfo>('/templates', { id, source }),
  deleteTemplate: (id: string) => request<{ status: string }>(`/templates/${id}`, { method: 'DELETE' }),
  metrics: () => request<Metrics>('/metrics'),
  runBenchmark: () => post<Benchmark>('/benchmark', {}),
}
