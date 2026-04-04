export default function DecisionBadge({ decision }) {
  const normalized = (decision || "PENDING").toLowerCase();
  return <span className={`decision-badge ${normalized}`}>{decision || "PENDING"}</span>;
}
