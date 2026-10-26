export type FieldKind = 'money' | 'percent' | 'integer' | 'date' | 'choice' | 'boolean' | 'text'
export type Origin = 'text' | 'answer' | 'default' | 'registry'
export type CheckStatus = 'passed' | 'warning' | 'failed' | 'skipped'
export type CheckGroup = 'arithmetic' | 'calendar' | 'regulatory' | 'contract' | 'analysis'
export type FieldRaw = string | number | boolean

export interface Choice {
  value: FieldRaw
  label: string
}

export interface FieldDef {
  key: string
  label: string
  group: string
  kind: FieldKind
  question: string
  hint: string | null
  choices: Choice[]
  default: FieldRaw | null
}

export interface FieldValue {
  value: FieldRaw
  origin: Origin
  evidence?: string | null
}

export type Values = Record<string, FieldValue>

export interface Issuer {
  inn: string
  ogrn: string
  full_name: string
  short_name: string
  code: string
  address: string
  director: string
  website: string
  rating: string | null
}

export interface Example {
  title: string
  inn: string
  text: string
}

export interface Meta {
  groups: string[]
  fields: FieldDef[]
  examples: Example[]
  issuers: Issuer[]
  faults: { value: string; label: string }[]
  provider: string
}

export interface Question {
  key: string
  text: string
  hint: string | null
  kind: FieldKind
  choices: Choice[]
}

export interface Draft {
  provider: string
  values: Values
  questions: Question[]
  issuer: Issuer | null
  notes: string[]
}

export interface Check {
  id: string
  group: CheckGroup
  title: string
  status: CheckStatus
  detail: string
  rows: Record<string, string>[]
  reference: string | null
}

export interface Period {
  number: number
  start: string
  end: string
  days: number
  coupon: string
  principal: string
  payment: string
  payment_date: string
  shifted: boolean
}

export interface Spec {
  issue_number: string
  issuer: Issuer
  nominal: string
  price: string
  min_quantity: number
  max_quantity: number
  min_amount: string
  max_amount: string
  book_start: string
  book_end: string
  issue_date: string
  maturity_date: string
  term_days: number
  coupon_rate: string
  coupon_frequency: string
  business_day_rule: string
  rounding_mode: string
  early_redemption: boolean
  investors: string
  allocation: string
}

export type Summary = Record<CheckStatus, number>

export interface FaultRun {
  fault: string
  label: string
  caught: boolean
  failed_checks: string[]
  created_at: string
}

export interface IssuePackage {
  id: string
  created_at: string
  text: string
  provider: string
  template: { id: string; title: string }
  spec: Spec
  values: Values
  schedule: Period[]
  totals: { coupon: string; payment: string; simple_yield: string }
  document: string
  contract: { name: string; source: string }
  compiler: string | null
  checks: Check[]
  summary: Summary
  fault_runs: FaultRun[]
  metrics: {
    preparation_seconds: number | null
    fields_total: number
    from_text: number
    from_answers: number
    from_defaults: number
    questions_asked: number
  }
}

export interface IssueListItem {
  id: string
  created_at: string
  issue_number: string
  issuer: string
  max_amount: string
  coupon_rate: string
  maturity_date: string
  summary: Summary
  preparation_seconds: number | null
}

export interface FaultResult extends FaultRun {
  diff: string[]
  checks: Check[]
}

export interface TemplateInfo {
  id: string
  title: string
  description: string
  builtin: boolean
  source: string
  variables: string[]
}

export interface Benchmark {
  created_at: string
  dataset: string
  source: string
  provider: string
  cases: number
  exact_cases: number
  fields_expected: number
  fields_correct: number
  recall: number
  precision: number
  per_field: { key: string; label: string; expected: number; correct: number }[]
  failures: { text: string; errors: { field: string; expected: string | null; actual: string | null }[] }[]
}

export interface Metrics {
  issues: number
  median_preparation_seconds: number | null
  fields: Partial<Record<'fields_total' | 'from_text' | 'from_answers' | 'from_defaults' | 'questions_asked', number>>
  avg_questions: number | null
  checks: Partial<Summary>
  fault_runs: number
  faults_caught: number
  timeline: { created_at: string; issue_number: string; preparation_seconds: number | null; questions_asked: number }[]
  benchmark: Benchmark | null
}

export interface SystemInfo {
  llm: { provider: string; label: string; model: string | null; endpoint: string | null }
  toolchain: { solc: string | null; slither: boolean; evm: string }
  storage: string
  external_hosts: string[]
  operator: { name: string; website: string }
}
