import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { ErrorState, Loading } from "../components/AsyncState";
import StatusPill from "../components/StatusPill";
import Table from "../components/Table";
import { formatDate, labelize } from "../utils";

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const load = useCallback(async () => {
    setError(null);
    try {
      const [kpis, recent] = await Promise.all([api.analytics.kpis(), api.applications.list({ page: 1, page_size: 6 })]);
      setData({ kpis, recent: recent.items });
    } catch (loadError) { setError(loadError); }
  }, []);
  useEffect(() => { load(); }, [load]);
  if (error) return <ErrorState error={error} retry={load} />;
  if (!data) return <Loading />;
  const { kpis, recent } = data;
  return <>
    <section className="kpi-grid">
      <div className="kpi"><span>Applications</span><strong>{kpis.total_applications}</strong></div>
      <div className="kpi"><span>Pending</span><strong>{kpis.pending_applications}</strong></div>
      <div className="kpi"><span>Approved</span><strong>{kpis.approved_applications}</strong></div>
      <div className="kpi"><span>Certificates</span><strong>{kpis.certificates_issued}</strong></div>
    </section>
    <section className="module-strip">
      <article className="module-card"><h3>Applications</h3><p>Registration cases, workflow, documents, and certificates.</p></article>
      <article className="module-card"><h3>Applicants</h3><p>Citizen and representative profiles.</p></article>
      <article className="module-card"><h3>Survey</h3><p>Surveyors, field milestones, reports, and registrar review.</p></article>
      <article className="module-card"><h3>Maps</h3><p>GeoJSON parcel locations and application status.</p></article>
    </section>
    <section className="page-section"><div className="section-header"><div><h2>Recent applications</h2><p>Latest submitted records</p></div><a className="button secondary" href="#applications">Open</a></div><div className="section-body"><Table rows={recent} empty="No applications available yet." columns={[
      { label: "Application", render: (row) => <strong>{row.application_id}</strong> },
      { label: "Type", render: (row) => labelize(row.application_type) },
      { label: "Status", render: (row) => <StatusPill status={row.status} /> },
      { label: "Parcel", render: (row) => row.parcel_ref?.parcel_number },
      { label: "Submitted", render: (row) => formatDate(row.timestamps?.submitted_at) },
    ]} /></div></section>
  </>;
}
