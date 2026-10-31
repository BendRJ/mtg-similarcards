export default function Loading({ count = 12 }: { count?: number }) {
  return (
    <div className="grid" aria-busy="true" aria-label="Loading">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="tile tile-skeleton" />
      ))}
    </div>
  );
}
