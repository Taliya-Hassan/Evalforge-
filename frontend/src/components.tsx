import { ReactNode } from "react";

export const pct = (x: number): string => `${(x * 100).toFixed(0)}%`;

export function Pill({ kind, children }: { kind: string; children: ReactNode }) {
  return <span className={`pill pill-${kind}`}>{children}</span>;
}

export function ErrorMsg({ message }: { message: string | null }) {
  return message ? <p className="error">{message}</p> : null;
}

export function Card({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <section className="card">
      {title && <h2>{title}</h2>}
      {children}
    </section>
  );
}
