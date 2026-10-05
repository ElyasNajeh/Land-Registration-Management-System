export function Loading({ label = "Loading…" }) { return <div className="empty-state" aria-live="polite">{label}</div>; }
export function ErrorState({ error, retry }) {
  return <div className="empty-state error-state"><strong>Unable to load this view</strong><p>{error?.message || "An unexpected error occurred."}</p>{retry && <button className="button secondary" onClick={retry}>Try again</button>}</div>;
}
