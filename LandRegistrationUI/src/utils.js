export function labelize(value) { return String(value ?? "Not set").replaceAll("_", " "); }
export function formatDate(value) {
  if (!value) return "Not recorded";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
}
export function statusClass(status) {
  if (["approved", "certificate_issued", "closed", "surveyed"].includes(status)) return "success";
  if (["on_hold", "missing_documents", "under_objection", "needs_correction"].includes(status)) return "warning";
  return status === "rejected" ? "danger" : "info";
}
export function splitList(value) { return String(value || "").split(",").map((item) => item.trim()).filter(Boolean); }
export function escapeHtml(value) {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}
