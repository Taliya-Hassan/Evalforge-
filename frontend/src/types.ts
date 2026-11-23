export interface Project { id: string; name: string; description: string | null; created_at: string }
export interface ModelCfg {
  id: string; project_id: string; name: string; provider: string;
  model_identifier: string; params: Record<string, unknown>;
}
export interface Suite { id: string; project_id: string; name: string; description: string | null }
export interface Case {
  id: string; suite_id: string; name: string; prompt: string;
  expected_output: string | null; scorer: string; threshold: number;
}
export interface Run {
  id: string; suite_id: string; model_id: string; status: string;
  created_at: string; started_at: string | null; finished_at: string | null;
}
export interface Result {
  test_case_id: string; test_case_name: string; output: string | null;
  score: number | null; passed: boolean | null; latency_ms: number | null; error: string | null;
}
export interface Summary {
  total: number; passed: number; failed: number; errors: number; pass_rate: number;
  mean_score: number; latency_p50_ms: number | null; latency_p95_ms: number | null;
}
export interface RunDetail extends Run { summary: Summary; results: Result[] }
export type DiffStatus = "regressed" | "improved" | "unchanged" | "new" | "missing";
export interface DiffItem {
  test_case_id: string; name: string; prompt: string; status: DiffStatus;
  baseline_passed: boolean | null; candidate_passed: boolean | null;
  baseline_score: number | null; candidate_score: number | null; score_delta: number | null;
  baseline_output: string | null; candidate_output: string | null;
  baseline_error: string | null; candidate_error: string | null;
}
export interface Diff {
  suite_id: string; baseline_run_id: string; candidate_run_id: string;
  counts: Record<DiffStatus, number>;
  baseline_pass_rate: number; candidate_pass_rate: number; pass_rate_delta: number;
  items: DiffItem[];
}
