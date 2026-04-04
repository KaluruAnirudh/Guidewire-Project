export function formatMoney(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
}


export function formatSignedMoney(value) {
  const numericValue = Number(value || 0);
  const prefix = numericValue > 0 ? "+" : numericValue < 0 ? "-" : "";
  return `${prefix}${formatMoney(Math.abs(numericValue))}`;
}


export function formatDate(value) {
  if (!value) {
    return "N/A";
  }

  return new Date(value).toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}


export function formatScore(value) {
  return Number(value || 0).toFixed(2);
}
