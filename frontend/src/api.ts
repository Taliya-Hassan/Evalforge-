const BASE: string = import.meta.env.VITE_API_URL ?? "/api";
const KEY = "evalforge_token";

export const getToken = (): string | null => localStorage.getItem(KEY);
export const setToken = (t: string | null): void => {
  if (t) localStorage.setItem(KEY, t);
  else localStorage.removeItem(KEY);
};

export async function api<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401 && token) {
      setToken(null);
      window.location.href = "/login";
    }
    const detail = data?.detail;
    if (typeof detail === "string") throw new Error(detail);
    if (Array.isArray(detail)) {
      throw new Error(detail.map((d: { msg: string }) => d.msg).join(", "));
    }
    throw new Error(`Request failed (${res.status})`);
  }
  return data as T;
}
