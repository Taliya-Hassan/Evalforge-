import { FormEvent, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { Card, ErrorMsg, Pill } from "../components";
import { useFetch } from "../hooks";
import { Case, ModelCfg, Run, Suite } from "../types";

const active = (runs: Run[]) => runs.some((r) => r.status === "queued" || r.status === "running");

export default function SuiteDetail() {
  const { suiteId } = useParams();
  const nav = useNavigate();
  const suite = useFetch<Suite>(`/suites/${suiteId}`);
  const cases = useFetch<Case[]>(`/suites/${suiteId}/cases`);
  const runs = useFetch<Run[]>(`/suites/${suiteId}/runs`, active);
  const models = useFetch<ModelCfg[]>(
    suite.data ? `/projects/${suite.data.project_id}/models` : null,
  );

  const [name, setName] = useState("");
  const [prompt, setPrompt] = useState("");
  const [expected, setExpected] = useState("");
  const [scorer, setScorer] = useState("contains");
  const [threshold, setThreshold] = useState("1");
  const [modelId, setModelId] = useState("");
  const [base, setBase] = useState("");
  const [cand, setCand] = useState("");
  const [error, setError] = useState<string | null>(null);

  const modelName = (id: string) => models.data?.find((m) => m.id === id)?.name ?? id.slice(0, 8);
  const done = (runs.data ?? []).filter((r) => r.status === "completed");

  async function addCase(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api(`/suites/${suiteId}/cases`, "POST", {
        name, prompt, expected_output: expected || null, scorer, threshold: Number(threshold),
      });
      setName(""); setPrompt(""); setExpected("");
      cases.reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function removeCase(id: string) {
    await api(`/cases/${id}`, "DELETE");
    cases.reload();
  }

  async function startRun() {
    setError(null);
    try {
      const run = await api<Run>(`/suites/${suiteId}/runs`, "POST", {
        model_id: modelId || models.data?.[0]?.id,
      });
      nav(`/runs/${run.id}`);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <>
      <p>
        {suite.data && <Link to={`/projects/${suite.data.project_id}`}>← Project</Link>}
      </p>
      <h1>{suite.data?.name ?? "…"}</h1>
      <ErrorMsg message={error ?? suite.error} />

      <Card title="Run this suite">
        {models.data?.length === 0 && (
          <p className="muted">Add a model to the project first (use “mock” to try it for free).</p>
        )}
        <div className="row">
          <select value={modelId} onChange={(e) => setModelId(e.target.value)}>
            {models.data?.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
          </select>
          <button onClick={startRun} disabled={!models.data?.length || !cases.data?.length}>
            Run
          </button>
        </div>
      </Card>

      <Card title="Runs">
        {runs.data?.length === 0 && <p className="muted">No runs yet.</p>}
        {runs.data?.map((r) => (
          <div key={r.id} className="row between">
            <Link to={`/runs/${r.id}`}>
              {modelName(r.model_id)} · {new Date(r.created_at).toLocaleString()}
            </Link>
            <Pill kind={r.status}>{r.status}</Pill>
          </div>
        ))}
        {done.length >= 2 && (
          <div className="stack top-gap">
            <Link to={`/suites/${suiteId}/diff`}><strong>Compare latest two runs →</strong></Link>
            <div className="row">
              <select value={base} onChange={(e) => setBase(e.target.value)}>
                <option value="">Baseline…</option>
                {done.map((r) => <option key={r.id} value={r.id}>{modelName(r.model_id)} · {new Date(r.created_at).toLocaleTimeString()}</option>)}
              </select>
              <select value={cand} onChange={(e) => setCand(e.target.value)}>
                <option value="">Candidate…</option>
                {done.map((r) => <option key={r.id} value={r.id}>{modelName(r.model_id)} · {new Date(r.created_at).toLocaleTimeString()}</option>)}
              </select>
              <button disabled={!base || !cand}
                      onClick={() => nav(`/suites/${suiteId}/diff?baseline=${base}&candidate=${cand}`)}>
                Compare
              </button>
            </div>
          </div>
        )}
      </Card>

      <Card title="Test cases">
        <form onSubmit={addCase} className="stack">
          <input placeholder="Case name" value={name} onChange={(e) => setName(e.target.value)} required />
          <textarea rows={2} placeholder="Prompt sent to the model" value={prompt}
                    onChange={(e) => setPrompt(e.target.value)} required />
          <input placeholder="Expected output (or regex pattern)" value={expected}
                 onChange={(e) => setExpected(e.target.value)} />
          <div className="row">
            <select value={scorer} onChange={(e) => setScorer(e.target.value)}>
              <option value="exact_match">exact_match</option>
              <option value="contains">contains</option>
              <option value="regex">regex</option>
              <option value="llm_judge">llm_judge</option>
            </select>
            <label className="muted">pass threshold
              <input type="number" min="0" max="1" step="0.1" value={threshold}
                     onChange={(e) => setThreshold(e.target.value)} style={{ width: 70, marginLeft: 6 }} />
            </label>
            <button type="submit">Add case</button>
          </div>
        </form>
        {cases.data?.map((c) => (
          <div key={c.id} className="case">
            <div className="row between">
              <strong>{c.name}</strong>
              <span><Pill kind="neutral">{c.scorer}</Pill>{" "}
                <button className="link" onClick={() => removeCase(c.id)}>delete</button></span>
            </div>
            <div className="muted">{c.prompt}</div>
            {c.expected_output && <div>expects: <code>{c.expected_output}</code></div>}
          </div>
        ))}
      </Card>
    </>
  );
}
