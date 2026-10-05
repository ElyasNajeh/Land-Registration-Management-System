import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { SURVEY_MILESTONES } from "../constants";
import { ErrorState, Loading } from "../components/AsyncState";
import Field from "../components/Field";
import Pagination from "../components/Pagination";
import StatusPill from "../components/StatusPill";
import Table from "../components/Table";
import { formatDate, labelize } from "../utils";

const formObject = (form) => Object.fromEntries(new FormData(form).entries());

export default function AssignmentsPage({ notify }) {
  const [result, setResult] = useState(null); const [error, setError] = useState(null); const [page, setPage] = useState(1); const [status, setStatus] = useState(""); const [refresh, setRefresh] = useState(0);
  const load = useCallback(() => { setError(null); api.assignments.list({ page, page_size: 20, status }).then(setResult).catch(setError); }, [page, status]);
  useEffect(() => { load(); }, [load, refresh]);
  const run = async (operation, message, form) => { try { await operation(); notify(message); form?.reset(); setRefresh((value) => value + 1); } catch (actionError) { notify(actionError.message, "error"); } };
  return <>
    <section className="page-section"><div className="section-header"><div><h2>Survey tasks</h2><p>Assigned tasks and current field milestone.</p></div><select value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}><option value="">All milestones</option>{["assigned", ...SURVEY_MILESTONES, "report_uploaded", "registrar_reviewed"].map((value) => <option key={value} value={value}>{labelize(value)}</option>)}</select></div><div className="section-body">{error ? <ErrorState error={error} retry={load} /> : !result ? <Loading /> : <><Table rows={result.items} empty="No survey tasks found." columns={[{ label: "Task", key: "task_id" }, { label: "Application", key: "application_id" }, { label: "Surveyor", key: "assigned_surveyor_name" }, { label: "Zone", key: "zone_id" }, { label: "Priority", key: "priority" }, { label: "Milestone", render: (row) => <StatusPill status={row.status} /> }, { label: "Updated", render: (row) => formatDate(row.updated_at) }]} /><Pagination page={result.page} pages={result.pages} total={result.total} onChange={setPage} /></>}</div></section>
    <section className="page-grid">
      <ActionCard title="Auto-assign surveyor" note="Requires survey_required status and a matching active surveyor."><form className="form-grid" onSubmit={(event) => { event.preventDefault(); const raw = formObject(event.currentTarget); run(() => api.assignments.autoAssign(raw.application_id), "Surveyor assigned", event.currentTarget); }}><Field label="Application ID" name="application_id" full required /><Submit label="Auto-assign" /></form></ActionCard>
      <ActionCard title="Survey milestone" note="Milestones must be recorded in sequence."><form className="form-grid" onSubmit={(event) => { event.preventDefault(); const raw = formObject(event.currentTarget); run(() => api.assignments.milestone(raw.application_id, { milestone_type: raw.milestone_type, by: raw.by, meta: raw.note ? { note: raw.note } : {} }), "Milestone added", event.currentTarget); }}><Field label="Application ID" name="application_id" required /><Field label="Milestone" name="milestone_type" options={SURVEY_MILESTONES} /><Field label="Recorded by" name="by" options={["surveyor", "system", "registrar"]} /><Field label="Note" name="note" /><Submit label="Add milestone" /></form></ActionCard>
      <ActionCard title="Survey report" note="Available after the survey_completed milestone."><form className="form-grid" onSubmit={(event) => { event.preventDefault(); const raw = formObject(event.currentTarget); run(() => api.assignments.report(raw.application_id, { uploaded_by: raw.uploaded_by, report_title: raw.report_title, summary: raw.summary, file_name: raw.file_name, file_url: raw.file_url || null }), "Survey report registered", event.currentTarget); }}><Field label="Application ID" name="application_id" required /><Field label="Uploaded by" name="uploaded_by" required /><Field label="Report title" name="report_title" required /><Field label="File name" name="file_name" required /><Field label="File URL (optional)" name="file_url" full /><Field label="Summary" name="summary" type="textarea" full required /><Submit label="Register report" /></form></ActionCard>
      <ActionCard title="Registrar review" note="Approves, rejects, or returns a completed survey for correction."><form className="form-grid" onSubmit={(event) => { event.preventDefault(); const raw = formObject(event.currentTarget); run(() => api.assignments.review(raw.application_id, { reviewed_by: raw.reviewed_by, decision: raw.decision, notes: raw.notes }), "Registrar review submitted", event.currentTarget); }}><Field label="Application ID" name="application_id" required /><Field label="Reviewed by" name="reviewed_by" required /><Field label="Decision" name="decision" options={["approved", "rejected", "needs_correction"]} /><Field label="Notes" name="notes" type="textarea" full required /><Submit label="Submit review" /></form></ActionCard>
    </section>
  </>;
}

function ActionCard({ title, note, children }) { return <article className="page-section span-6"><div className="section-header"><div><h2>{title}</h2><p>{note}</p></div></div><div className="section-body">{children}</div></article>; }
function Submit({ label }) { return <div className="form-field full"><button className="button">{label}</button></div>; }
