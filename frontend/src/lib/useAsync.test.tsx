import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useAsync } from "./useAsync";

function deferred<T>() {
  let resolve!: (v: T) => void;
  let reject!: (e: unknown) => void;
  const promise = new Promise<T>((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

describe("useAsync", () => {
  it("ignores a stale result and aborts the previous load", async () => {
    const first = deferred<string>();
    const second = deferred<string>();
    const signals: AbortSignal[] = [];
    const { result, rerender } = renderHook(
      ({ id }) => useAsync((signal) => { signals.push(signal); return id === 1 ? first.promise : second.promise; }, [id]),
      { initialProps: { id: 1 } },
    );
    expect(result.current.status).toBe("loading");
    rerender({ id: 2 });
    expect(signals[0].aborted).toBe(true);
    await act(async () => { second.resolve("two"); });
    await act(async () => { first.resolve("one"); });
    await waitFor(() => expect(result.current.status).toBe("ok"));
    expect(result.current.data).toBe("two");
  });

  it("reports errors", async () => {
    const err = new Error("x");
    const { result } = renderHook(() => useAsync(() => Promise.reject(err), []));
    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe(err);
  });

  it("aborts on unmount and sets no state afterwards", async () => {
    const d = deferred<string>();
    let signal!: AbortSignal;
    const spy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    const { unmount } = renderHook(() => useAsync((s) => { signal = s; return d.promise; }, []));
    unmount();
    expect(signal.aborted).toBe(true);
    await act(async () => { d.resolve("late"); });
    expect(spy).not.toHaveBeenCalled();
  });

  it("reload re-runs the load", async () => {
    const load = vi.fn().mockResolvedValueOnce("a").mockResolvedValueOnce("b");
    const { result } = renderHook(() => useAsync(load, []));
    await waitFor(() => expect(result.current.data).toBe("a"));
    act(() => result.current.reload());
    expect(result.current.status).toBe("loading");
    await waitFor(() => expect(result.current.data).toBe("b"));
    expect(load).toHaveBeenCalledTimes(2);
  });
});
