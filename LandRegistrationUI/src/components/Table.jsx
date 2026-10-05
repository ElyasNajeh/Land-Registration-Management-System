export default function Table({ columns, rows, empty = "No records found." }) {
  if (!rows?.length) return <div className="empty-state">{empty}</div>;
  return <div className="table-wrap"><table className="data-table"><thead><tr>{columns.map((column) => <th key={column.key || column.label}>{column.label}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={row._id || row.application_id || row.task_id || index}>{columns.map((column) => <td key={column.key || column.label}>{column.render ? column.render(row) : row[column.key]}</td>)}</tr>)}</tbody></table></div>;
}
