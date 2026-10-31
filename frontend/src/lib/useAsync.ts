import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api";

type State<T> = { status: "loading" | "ok" | "error"; data: T | null; error: ApiError | null };

export function useAsync<T>(load: (signal: AbortSignal) => Promise<T>, deps: unknown[]) {
  const [state, setState] = useState<State<T>>({ status: "loading", data: null, error: null });
  const [reloadCount, setReloadCount] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading", data: null, error: null });
    load(controller.signal).then(
      (data) => {
        if (!controller.signal.aborted) setState({ status: "ok", data, error: null });
      },
      (error) => {
        if (!controller.signal.aborted) setState({ status: "error", data: null, error });
      },
    );
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, reloadCount]);

  const reload = useCallback(() => setReloadCount((n) => n + 1), []);
  return { ...state, reload };
}
