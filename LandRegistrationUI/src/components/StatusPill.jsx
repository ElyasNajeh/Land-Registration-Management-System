import { labelize, statusClass } from "../utils";

export default function StatusPill({ status }) {
  return <span className={`status-pill ${statusClass(status)}`}>{labelize(status)}</span>;
}
