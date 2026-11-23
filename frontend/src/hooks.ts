import { useCallback, useEffect, useState } from "react";
import { api } from "./api";

/** GET `path` (skip when null). Re-polls every 1.5s while keepPolling(data) is true. */
export function useFetch<T>(path: string | null, keepPolling?: (d: T) => boolean) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const reload = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    if (path === null) return;
    let cancelled = false;
    let timer: number | undefined;
    const load = async () => {
      try {
        const d = await api<T>(path);
        if (cancelled) return;
        setData(d);
        setError(null);
        if (keepPolling?.(d)) timer = window.setTimeout(load, 1500);
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      }
    };
    load();
    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, tick]);

  return { data, error, reload };
}
