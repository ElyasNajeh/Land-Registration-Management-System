export default function Pagination({ page, pages, total, onChange }) {
  if (!total) return null;
  return <div className="pagination"><span>{total} record{total === 1 ? "" : "s"}</span><div className="button-row"><button className="button secondary compact" disabled={page <= 1} onClick={() => onChange(page - 1)}>Previous</button><span>Page {page} of {Math.max(pages, 1)}</span><button className="button secondary compact" disabled={page >= pages} onClick={() => onChange(page + 1)}>Next</button></div></div>;
}
