import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Card, ErrorMsg } from "../components";
import { useFetch } from "../hooks";
import { Project } from "../types";

export default function Projects() {
  const { data, error, reload } = useFetch<Project[]>("/projects");
  const [name, setName] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  async function create(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    try {
      await api("/projects", "POST", { name });
      setName("");
      reload();
    } catch (err) {
      setFormError((err as Error).message);
    }
  }

  return (
    <>
      <h1>Projects</h1>
      <ErrorMsg message={error} />
      <Card>
        <form onSubmit={create} className="row">
          <input placeholder="New project name" value={name}
                 onChange={(e) => setName(e.target.value)} required />
          <button type="submit">Create</button>
        </form>
        <ErrorMsg message={formError} />
      </Card>
      {data?.length === 0 && <p className="muted">No projects yet. Create your first one above.</p>}
      {data?.map((p) => (
        <Card key={p.id}>
          <Link to={`/projects/${p.id}`}><strong>{p.name}</strong></Link>
          {p.description && <p className="muted">{p.description}</p>}
        </Card>
      ))}
    </>
  );
}
