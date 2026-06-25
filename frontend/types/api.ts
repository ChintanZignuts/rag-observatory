export type Overview = {
  documents_count: number
  chunks_count: number
  questions_count: number
  latest_evaluation_run: EvaluationRunSummary | null
}

export type EvaluationRunSummary = {
  id: number
  name: string
  status: string
  started_at: string | null
  completed_at: string | null
  average_context_precision: number | null
  average_faithfulness: number | null
  average_answer_relevance: number | null
  results_count?: number
  created_at: string
}

export type EvaluationRunsResponse = {
  results: EvaluationRunSummary[]
}

export type EvaluationRunDetail = EvaluationRunSummary & {
  notes: string
  results: EvaluationResult[]
}

export type EvaluationResult = {
  id: number
  question_id: string
  category: string
  difficulty: string
  question: string
  expected_answer: string
  generated_answer: string
  context_precision: number | null
  faithfulness: number | null
  answer_relevance: number | null
  error_message: string
  retrieved_context: RetrievedContext[]
}

export type RetrievedContext = {
  chunk_id: number
  score: number
  document: string
  category: string
  page_number: number | null
  chunk_index: number
  text: string
}

export type AskResponse = {
  id: number
  question: string
  answer: string
  sources: Array<{
    document: string
    page_number: number | null
    score: number
    chunk_id: number
  }>
  latency_ms: number
  prompt_tokens: number | null
  completion_tokens: number | null
}
