import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { ErrorState, Loading } from "../components/AsyncState";
import Table from "../components/Table";
import { labelize } from "../utils";

function Distribution({ title, rows }) {
  const total = rows.reduce((sum, row) => sum + row.count, 0) || 1;
  return <article className="page-section span-6"><div className="section-header"><div><h2>{title}</h2><p>Calculated by MongoDB aggregation.</p></div></div><div className="section-body zone-list">{rows.length ? rows.map((row) => <div className="zone-row" key={row.key}><span>{labelize(row.key)}</span><strong>{row.count} ({Math.round(row.count / total * 100)}%)</strong></div>) : <div className="empty-state">No data available.</div>}</div></article>;
}

export default function AnalyticsPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const load = useCallback(async () => {
    setError(null);
    try {
      const [kpis, statuses, types, zones, processing, surveyors] = await Promise.all([api.analytics.kpis(), api.analytics.status(), api.analytics.types(), api.analytics.zones(), api.analytics.processing(), api.analytics.surveyors()]);
      setData({ kpis, statuses, types, zones, processing, surveyors });
    } catch (loadError) { setError(loadError); }
  }, []);
  useEffect(() => { load(); }, [load]);
  if (error) return <ErrorState error={error} retry={load} />;
  if (!data) return <Loading label="Loading analytics…" />;
  return <>
    <section className="kpi-grid">
      <div className="kpi"><span>Total applications</span><strong>{data.kpis.total_applications}</strong></div>
      <div className="kpi"><span>Pending</span><strong>{data.kpis.pending_applications}</strong></div>
      <div className="kpi"><span>Under objection</span><strong>{data.kpis.under_objection}</strong></div>
      <div className="kpi"><span>Approval rate</span><strong>{data.kpis.approval_rate}%</strong></div>
    </section>
    <section className="page-grid"><Distribution title="Status distribution" rows={data.statuses} /><Distribution title="Application type mix" rows={data.types} />
      <article className="page-section span-6"><div className="section-header"><h2>Applications by zone</h2></div><div className="section-body"><Table rows={data.zones} columns={[{ label: "Zone", key: "key" }, { label: "Applications", key: "count" }]} /></div></article>
      <article className="page-section span-6"><div className="section-header"><h2>Surveyor workload</h2></div><div className="section-body"><Table rows={data.surveyors} columns={[{ label: "Surveyor", render: (row) => row.name }, { label: "Code", key: "staff_code" }, { label: "Active tasks", render: (row) => `${row.workload?.active_tasks || 0} / ${row.workload?.max_tasks || 0}` }]} /></div></article>
      <article className="page-section span-12"><div className="section-header"><h2>Average processing time</h2></div><div className="section-body"><Table rows={data.processing} columns={[{ label: "Application type", render: (row) => labelize(row.application_type) }, { label: "Average hours", key: "average_hours" }, { label: "Records", key: "count" }]} /></div></article>
    </section>
  </>;
}
