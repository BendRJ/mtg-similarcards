import type { ApiError } from "../api";

// The error is accepted for callers' convenience; the copy is the same for every failure.
export default function ErrorState({ onRetry }: { error: ApiError; onRetry: () => void }) {
  return (
    <div className="error-state" role="alert">
      <p>Couldn't reach the card database. Try again.</p>
      <button type="button" className="btn" onClick={onRetry}>
        Retry
      </button>
    </div>
  );
}
