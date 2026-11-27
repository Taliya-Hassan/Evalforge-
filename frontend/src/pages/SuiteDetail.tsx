import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { Card, ErrorMsg, Pill } from "../components";
import { useFetch } from "../hooks";
import { Case, ModelCfg, Run, Suite } from "../types";

type CaseRow = Case & { scorer_config?: Record<string, unknown> };
interface Draft { name: string; prompt: string; expected: string; scorer: string }

const SCORERS = ["exact_match", "contains", "regex", "llm_judge"];
const EMPTY: Draft = { name: "", prompt: "", expected: "", scorer: "contains" };
const full = { width: "100%", minWidth: 0 } as const;
const active = (runs: Run[]) => runs.some((r) => r.status === "queued" || r.status === "running");
const autoName = (d: Draft) => d.name.trim() || d.prompt.trim().slice(0, 40);

function DraftCells({ draft, onChange }: { draft: Draft; onChange: (d: Draft) => void }) {
  return (
    <>
      <td>
        <input style={full} placeholder="Name (optional)" value={draft.name}
               onChange={(e) => onChange({ ...draft, name: e.target.value })} />
      </td>
      <td>
        <textarea style={full} rows={2} placeholder="Input / prompt" value={draft.prompt}
                  onChange={(e) => onChange({ ...draft, prompt: e.target.value })} />
      </td>
      <td>
        <textarea style={full} rows={2} placeholder="Expected output" value={draft.expected}
                  onChange={(e) => onChange({ ...draft, expected: e.target.value })} />
      </td>
      <td>
        <select style={full} value={draft.scorer}
                onChange={(e) => onChange({ ...draft, scorer: e.target.value })}>
          {SCORERS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </td>
    </>
  );
}

function CasesTable(props: {
  suiteId: string | undefined;
  cases: CaseRow[] | null;
  reload: () => void;
  setError: (m: string | null) => void;
}) {
  const { suiteId, cases, reload, setError } = props;
  const [draft, setDraft] = useState<Draft>(EMPTY);
  const [editId, setEditId] = useState<string | null>(null);
  const [edit, setEdit] = useState<Draft>(EMPTY);

  async function add() {
    if (!draft.prompt.trim()) {
      setError("Input (prompt) is required");
      return;
    }
    setError(null);
    try {
      await api(`/suites/${suiteId}/cases`, "POST", {
        name: autoName(draft),
        prompt: draft.prompt,
        expected_output: draft.expected || null,
        scorer: draft.scorer,
      });
      setDraft(EMPTY);
      reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function startEdit(c: CaseRow) {
    setEditId(c.id);
    setEdit({ name: c.name, prompt: c.prompt, expected: c.expected_output ?? "", scorer: c.scorer });
  }

  async function save(c: CaseRow) {
    if (!edit.prompt.trim()) {
      setError("Input (prompt) is required");
      return;
    }
    setError(null);
    try {
      await api(`/cases/${c.id}`, "PUT", {
        name: autoName(edit),
        prompt: edit.prompt,
        expected_output: edit.expected || null,
        scorer: edit.scorer,
        scorer_config: c.scorer_config ?? {},
        threshold: c.threshold,
      });
      setEditId(null);
      reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function remove(c: CaseRow) {
    if (!window.confirm(`Delete case "${c.name}"?`)) return;
    setError(null);
    try {
      await api(`/cases/${c.id}`, "DELETE");
      reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div style={{ overflowX: "auto" }}>
      <table>
        <thead>
          <tr>
            <th>#</th><th>Name</th><th>Input (prompt)</th><th>Expected output</th>
            <th>Scorer</th><th></th>
          </tr>
        </thead>
        <tbody>
          {(cases ?? []).map((c, i) =>
            editId === c.id ? (
              <tr key={c.id}>
                <td>{i + 1}</td>
                <DraftCells draft={edit} onChange={setEdit} />
                <td style={{ whiteSpace: "nowrap" }}>
                  <button onClick={() => save(c)}>Save</button>{" "}
                  <button className="link" onClick={() => setEditId(null)}>Cancel</button>
                </td>
              </tr>
            ) : (
              <tr key={c.id}>
                <td>{i + 1}</td>
                <td>{c.name}</td>
                <td className="out">{c.prompt}</td>
                <td className="out">{c.expected_output ?? "–"}</td>
                <td><Pill kind="neutral">{c.scorer}</Pill></td>
                <td style={{ whiteSpace: "nowrap" }}>
                  <button className="link" onClick={() => startEdit(c)}>edit</button>{" "}
                  <button className="link" onClick={() => remove(c)}>delete</button>
                </td>
              </tr>
            ),
          )}
          <tr>
            <td>+</td>
            <DraftCells draft={draft} onChange={setDraft} />
            <td><button onClick={add}>Add</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

export default function SuiteDetail() {
  const { suiteId } = useParams();
  const nav = useNavigate();
  const suite = useFetch<Suite>(`/suites/${suiteId}`);
  const cases = useFetch<CaseRow[]>(`/suites/${suiteId}/cases`);
  const runs = useFetch<Run[]>(`/suites/${suiteId}/runs`, active);
  const models = useFetch<ModelCfg[]>(
    suite.data ? `/projects/${suite.data.project_id}/models` : null,
  );

  const [modelId, setModelId] = useState("");
  const [base, setBase] = useState("");
  const [cand, setCand] = useState("");
  const [error, setError] = useState<string | null>(null);

  const modelName = (id: string) => models.data?.find((m) => m.id === id)?.name ?? id.slice(0, 8);
  const done = (runs.data ?? []).filter((r) => r.status === "completed");

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
      <ErrorMsg message={error ?? suite.error ?? cases.error} />

      <Card title="Test cases">
        <p className="muted">Every change is saved to the database immediately.</p>
        <CasesTable suiteId={suiteId} cases={cases.data} reload={cases.reload} setError={setError} />
      </Card>

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
                {done.map((r) => (
                  <option key={r.id} value={r.id}>
                    {modelName(r.model_id)} · {new Date(r.created_at).toLocaleTimeString()}
                  </option>
                ))}
              </select>
              <select value={cand} onChange={(e) => setCand(e.target.value)}>
                <option value="">Candidate…</option>
                {done.map((r) => (
                  <option key={r.id} value={r.id}>
                    {modelName(r.model_id)} · {new Date(r.created_at).toLocaleTimeString()}
                  </option>
                ))}
              </select>
              <button disabled={!base || !cand}
                      onClick={() => nav(`/suites/${suiteId}/diff?baseline=${base}&candidate=${cand}`)}>
                Compare
              </button>
            </div>
          </div>
        )}
      </Card>
    </>
  );
}