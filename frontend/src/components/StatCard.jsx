export default function StatCard({ label, value, accent = "default" }) {
  return (
    <article className={`stat-card ${accent}`}>
      <p>{label}</p>
      <strong>{value}</strong>
    </article>
  );
}

