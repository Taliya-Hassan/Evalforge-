import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, setToken } from "../api";
import { ErrorMsg } from "../components";

export default function Login() {
  const nav = useNavigate();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (mode === "signup") await api("/auth/signup", "POST", { email, password });
      const t = await api<{ access_token: string }>("/auth/login", "POST", { email, password });
      setToken(t.access_token);
      nav("/");
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="auth">
      <h1>EvalForge</h1>
      <p className="muted">Regression testing for LLM features</p>
      <form onSubmit={submit} className="stack">
        <input type="email" placeholder="Email" value={email}
               onChange={(e) => setEmail(e.target.value)} required />
        <input type="password" placeholder="Password (min 8 characters)" value={password}
               onChange={(e) => setPassword(e.target.value)} minLength={8} required />
        <ErrorMsg message={error} />
        <button type="submit">{mode === "login" ? "Log in" : "Create account"}</button>
      </form>
      <button className="link" onClick={() => setMode(mode === "login" ? "signup" : "login")}>
        {mode === "login" ? "Need an account? Sign up" : "Have an account? Log in"}
      </button>
    </div>
  );
}
