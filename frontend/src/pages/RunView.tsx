import { Link, useParams } from "react-router-dom";
import { Card, ErrorMsg, Pill, pct } from "../components";
import { useFetch } from "../hooks";
import { RunDetail } from "../types";

const live = (r: RunDetail) => r.status === "queued" || r.status === "running";

export default function RunView() {
  const { runId } = useParams();
  const { data: run, error } = useFetch<RunDetail>(`/runs/${runId}`, live);

  if (!run) return <ErrorMsg message={error} />;
  const s = run.summary;
  return (
    <>
      <p><Link to={`/suites/${run.suite_id}`}>← Suite</Link></p>
      <h1>Run <Pill kind={run.status}>{run.status}</Pill></h1>
      <ErrorMsg message={error} />

      <div className="stats">
        <div><span>Pass rate</span><strong>{pct(s.pass_rate)}</strong></div>
        <div><span>Passed</span><strong>{s.passed}/{s.total}</strong></div>
        <div><span>Errors</span><strong>{s.errors}</strong></div>
        <div><span>Mean score</span><strong>{s.mean_score.toFixed(2)}</strong></div>
        <div><span>p50 / p95</span>
          <strong>{s.latency_p50_ms ?? "–"} / {s.latency_p95_ms ?? "–"} ms</strong></div>
      </div>

      <Card title="Results">
        <table>
          <thead><tr><th>Case</th><th>Result</th><th>Score</th><th>Output</th></tr></thead>
          <tbody>
            {run.results.map((r) => (
              <tr key={r.test_case_id}>
                <td>{r.test_case_name}</td>
                <td>{r.error ? <Pill kind="failed">error</Pill>
                  : <Pill kind={r.passed ? "completed" : "failed"}>{r.passed ? "pass" : "fail"}</Pill>}</td>
                <td>{r.score?.toFixed(2) ?? "–"}</td>
                <td className="out">{r.error ?? r.output}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {live(run) && <p className="muted">Running… this page refreshes automatically.</p>}
      </Card>
    </>
  );
}
