import { FormEvent, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { Card, ErrorMsg } from "../components";
import { useFetch } from "../hooks";
import { ModelCfg, Project, Suite } from "../types";

export default function ProjectDetail() {
  const { projectId } = useParams();
  const project = useFetch<Project>(`/projects/${projectId}`);
  const models = useFetch<ModelCfg[]>(`/projects/${projectId}/models`);
  const suites = useFetch<Suite[]>(`/projects/${projectId}/suites`);

  const [suiteName, setSuiteName] = useState("");
  const [mName, setMName] = useState("");
  const [provider, setProvider] = useState("mock");
  const [identifier, setIdentifier] = useState("");
  const [params, setParams] = useState("{}");
  const [error, setError] = useState<string | null>(null);

  async function addSuite(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api(`/projects/${projectId}/suites`, "POST", { name: suiteName });
      setSuiteName("");
      suites.reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function addModel(e: FormEvent) {
    e.preventDefault();
    setError(null);
    let parsed: unknown;
    try {
      parsed = JSON.parse(params);
    } catch {
      setError("Params must be valid JSON");
      return;
    }
    try {
      await api(`/projects/${projectId}/models`, "POST", {
        name: mName, provider, model_identifier: identifier, params: parsed,
      });
      setMName("");
      setIdentifier("");
      models.reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function removeModel(id: string) {
    setError(null);
    try {
      await api(`/models/${id}`, "DELETE");
      models.reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <>
      <p><Link to="/">← Projects</Link></p>
      <h1>{project.data?.name ?? "…"}</h1>
      <ErrorMsg message={error ?? project.error} />

      <Card title="Test suites">
        <form onSubmit={addSuite} className="row">
          <input placeholder="New suite name" value={suiteName}
                 onChange={(e) => setSuiteName(e.target.value)} required />
          <button type="submit">Add suite</button>
        </form>
        {suites.data?.map((s) => (
          <p key={s.id}><Link to={`/suites/${s.id}`}>{s.name}</Link></p>
        ))}
        {suites.data?.length === 0 && <p className="muted">No suites yet.</p>}
      </Card>

      <Card title="Models under test">
        <form onSubmit={addModel} className="stack">
          <div className="row">
            <input placeholder="Display name (e.g. v2 prompt)" value={mName}
                   onChange={(e) => setMName(e.target.value)} required />
            <select value={provider} onChange={(e) => setProvider(e.target.value)}>
              <option value="mock">mock (no API key)</option>
              <option value="openai">openai</option>
              <option value="anthropic">anthropic</option>
            </select>
            <input placeholder="Model id (e.g. gpt-4o-mini)" value={identifier}
                   onChange={(e) => setIdentifier(e.target.value)} required />
          </div>
          <textarea rows={3} value={params} onChange={(e) => setParams(e.target.value)}
                    placeholder='{"temperature": 0} or, for mock: {"responses": {"prompt": "answer"}}' />
          <button type="submit">Add model</button>
        </form>
        {models.data?.map((m) => (
          <div key={m.id} className="row between">
            <span><strong>{m.name}</strong> <span className="muted">
              {m.provider} · {m.model_identifier}</span></span>
            <button className="link" onClick={() => removeModel(m.id)}>delete</button>
          </div>
        ))}
      </Card>
    </>
  );
}
