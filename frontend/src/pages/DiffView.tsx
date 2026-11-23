import { Link, useParams, useSearchParams } from "react-router-dom";
import { Card, ErrorMsg, Pill, pct } from "../components";
import { useFetch } from "../hooks";
import { Diff, DiffStatus } from "../types";

const KIND: Record<DiffStatus, string> = {
  regressed: "failed", improved: "completed", unchanged: "neutral", new: "running", missing: "queued",
};

export default function DiffView() {
  const { suiteId } = useParams();
  const [qs] = useSearchParams();
  const b = qs.get("baseline");
  const c = qs.get("candidate");
  const query = b && c ? `?baseline=${b}&candidate=${c}` : "";
  const { data: d, error } = useFetch<Diff>(`/suites/${suiteId}/diff${query}`);

  const delta = d ? d.pass_rate_delta : 0;
  return (
    <>
      <p><Link to={`/suites/${suiteId}`}>← Suite</Link></p>
      <h1>Regression diff</h1>
      <ErrorMsg message={error} />
      {d && (
        <>
          <div className="stats">
            <div><span>Regressed</span><strong className="bad">{d.counts.regressed}</strong></div>
            <div><span>Improved</span><strong className="good">{d.counts.improved}</strong></div>
            <div><span>Unchanged</span><strong>{d.counts.unchanged}</strong></div>
            <div><span>Pass rate</span>
              <strong>{pct(d.baseline_pass_rate)} → {pct(d.candidate_pass_rate)}
                <small className={delta < 0 ? "bad" : delta > 0 ? "good" : ""}>
                  {" "}({delta > 0 ? "+" : ""}{(delta * 100).toFixed(0)} pts)</small></strong></div>
          </div>
          <Card>
            {d.items.map((i) => (
              <details key={i.test_case_id} className="diffrow" open={i.status === "regressed"}>
                <summary>
                  <Pill kind={KIND[i.status]}>{i.status}</Pill>{" "}
                  <strong>{i.name}</strong>
                  <span className="muted"> {i.baseline_score?.toFixed(2) ?? "–"} → {i.candidate_score?.toFixed(2) ?? "–"}</span>
                </summary>
                <p className="muted">Prompt: {i.prompt}</p>
                <div className="sbs">
                  <div><h4>Baseline {i.baseline_passed === null ? "" : i.baseline_passed ? "✓" : "✗"}</h4>
                    <pre>{i.baseline_error ?? i.baseline_output ?? "(no result)"}</pre></div>
                  <div><h4>Candidate {i.candidate_passed === null ? "" : i.candidate_passed ? "✓" : "✗"}</h4>
                    <pre>{i.candidate_error ?? i.candidate_output ?? "(no result)"}</pre></div>
                </div>
              </details>
            ))}
          </Card>
        </>
      )}
    </>
  );
}
