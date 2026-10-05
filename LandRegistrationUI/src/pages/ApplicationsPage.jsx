import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import { APPLICATION_STATUSES, APPLICATION_TYPES } from "../constants";
import { ErrorState, Loading } from "../components/AsyncState";
import Field from "../components/Field";
import Modal from "../components/Modal";
import Pagination from "../components/Pagination";
import StatusPill from "../components/StatusPill";
import Table from "../components/Table";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { formatDate, labelize, splitList } from "../utils";

const initialFilters = { search: "", status: "", application_type: "", zone_id: "", sort_field: "timestamps.submitted_at", sort_order: -1 };
const formObject = (form) => Object.fromEntries(new FormData(form).entries());

export default function ApplicationsPage({ notify }) {
  const [filters, setFilters] = useState(initialFilters);
  const [page, setPage] = useState(1);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const debouncedSearch = useDebouncedValue(filters.search);
  const requestId = useRef(0);
  const reload = useCallback(() => setRefreshKey((value) => value + 1), []);

  useEffect(() => {
    const current = ++requestId.current;
    setError(null);
    api.applications.list({ search: debouncedSearch, status: filters.status, application_type: filters.application_type, zone_id: filters.zone_id, sort_field: filters.sort_field, sort_order: filters.sort_order, page, page_size: 20 }).then((data) => {
      if (current === requestId.current) setResult(data);
    }).catch((loadError) => current === requestId.current && setError(loadError));
  }, [debouncedSearch, filters.status, filters.application_type, filters.zone_id, filters.sort_field, filters.sort_order, page, refreshKey]);

  const updateFilter = (event) => { setFilters((value) => ({ ...value, [event.target.name]: event.target.value })); setPage(1); };
  return <>
    <section className="page-section">
      <div className="section-header"><div><h2>Application management</h2><p>Search, filter, sort, and page at the database level.</p></div><button className="button" onClick={() => setCreateOpen(true)}>New application</button></div>
      <div className="section-body"><div className="filters">
        <input name="search" value={filters.search} onChange={updateFilter} placeholder="Search ID, description, or parcel" aria-label="Search applications" />
        <select name="status" value={filters.status} onChange={updateFilter}><option value="">All statuses</option>{APPLICATION_STATUSES.map((value) => <option key={value} value={value}>{labelize(value)}</option>)}</select>
        <select name="application_type" value={filters.application_type} onChange={updateFilter}><option value="">All types</option>{APPLICATION_TYPES.map((value) => <option key={value} value={value}>{labelize(value)}</option>)}</select>
        <input name="zone_id" value={filters.zone_id} onChange={updateFilter} placeholder="Zone" aria-label="Filter by zone" />
        <select name="sort_field" value={filters.sort_field} onChange={updateFilter}><option value="timestamps.submitted_at">Submitted date</option><option value="timestamps.updated_at">Updated date</option><option value="application_id">Application ID</option><option value="status">Status</option><option value="priority">Priority</option></select>
        <select name="sort_order" value={filters.sort_order} onChange={updateFilter}><option value="-1">Descending</option><option value="1">Ascending</option></select>
      </div></div>
      <div className="section-body">
        {error ? <ErrorState error={error} retry={reload} /> : !result ? <Loading /> : <><Table rows={result.items} empty="No applications match these filters." columns={[
          { label: "Application", render: (row) => <button className="link-button" onClick={() => setSelectedId(row.application_id)}>{row.application_id}</button> },
          { label: "Type", render: (row) => labelize(row.application_type) },
          { label: "Status", render: (row) => <StatusPill status={row.status} /> },
          { label: "Parcel", render: (row) => row.parcel_ref?.parcel_number || "—" },
          { label: "Zone", render: (row) => row.parcel_ref?.zone_id || "—" },
          { label: "Updated", render: (row) => formatDate(row.timestamps?.updated_at) },
        ]} /><Pagination page={result.page} pages={result.pages} total={result.total} onChange={setPage} /></>}
      </div>
    </section>
    {createOpen && <CreateApplicationModal onClose={() => setCreateOpen(false)} onCreated={(application) => { setCreateOpen(false); notify(`Application ${application.application_id} created`); reload(); }} notify={notify} />}
    {selectedId && <ApplicationDetail applicationId={selectedId} onClose={() => setSelectedId(null)} onChanged={reload} notify={notify} />}
  </>;
}

function CreateApplicationModal({ onClose, onCreated, notify }) {
  const [saving, setSaving] = useState(false);
  const submit = async (event) => {
    event.preventDefault(); setSaving(true);
    const raw = formObject(event.currentTarget);
    const lat = Number(raw.latitude); const lng = Number(raw.longitude);
    const payload = {
      application_type: raw.application_type, applicant_id: raw.applicant_id, parcel_id: raw.parcel_id,
      parcel_number: raw.parcel_number, block_number: raw.block_number, basin_number: raw.basin_number, zone_id: raw.zone_id,
      priority: raw.priority, description: raw.description || null,
      geometry: Number.isFinite(lat) && Number.isFinite(lng) ? { type: "Point", coordinates: [lng, lat] } : null,
      documents: raw.document_type && raw.file_name ? [{ document_type: raw.document_type, file_name: raw.file_name }] : [],
    };
    try { onCreated(await api.applications.create(payload, crypto.randomUUID())); }
    catch (error) { notify(error.message, "error"); setSaving(false); }
  };
  return <Modal title="Submit land application" onClose={onClose} wide><form className="form-grid" onSubmit={submit}>
    <Field label="Application type" name="application_type" options={APPLICATION_TYPES} required />
    <Field label="Applicant ID" name="applicant_id" required />
    <Field label="Parcel ID" name="parcel_id" required />
    <Field label="Parcel number" name="parcel_number" required />
    <Field label="Block number" name="block_number" required />
    <Field label="Basin number" name="basin_number" required />
    <Field label="Zone" name="zone_id" required />
    <Field label="Priority" name="priority" options={["low", "normal", "high", "urgent"]} defaultValue="normal" />
    <Field label="Latitude" name="latitude" type="number" step="any" placeholder="31.9038" required />
    <Field label="Longitude" name="longitude" type="number" step="any" placeholder="35.2034" required />
    <Field label="Description" name="description" type="textarea" full />
    <Field label="Initial document type (optional)" name="document_type" options={[{ value: "", label: "None" }, "ownership_deed", "id_copy", "sale_contract", "survey_report"]} />
    <Field label="Initial document file name" name="file_name" />
    <div className="form-field full"><button className="button" disabled={saving}>{saving ? "Submitting…" : "Submit application"}</button></div>
  </form></Modal>;
}

function ApplicationDetail({ applicationId, onClose, onChanged, notify }) {
  const [data, setData] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true);
    try { const [application, history] = await Promise.all([api.applications.get(applicationId), api.applications.timeline(applicationId)]); setData(application); setTimeline(history); }
    catch (error) { notify(error.message, "error"); onClose(); }
    finally { setLoading(false); }
  }, [applicationId, notify, onClose]);
  useEffect(() => { load(); }, [load]);
  const run = async (operation, message) => {
    try { await operation(); notify(message); await load(); onChanged(); }
    catch (error) { notify(error.message, "error"); }
  };
  return <Modal title={`Application ${applicationId}`} onClose={onClose} wide>{loading || !data ? <Loading /> : <>
    <dl className="detail-list">
      <div><dt>Status</dt><dd><StatusPill status={data.status} /></dd></div><div><dt>Type</dt><dd>{labelize(data.application_type)}</dd></div>
      <div><dt>Applicant</dt><dd>{data.applicant_ref?.applicant_id}</dd></div><div><dt>Parcel</dt><dd>{data.parcel_ref?.parcel_number} / Block {data.parcel_ref?.block_number}</dd></div>
      <div><dt>Zone</dt><dd>{data.parcel_ref?.zone_id}</dd></div><div><dt>Submitted</dt><dd>{formatDate(data.timestamps?.submitted_at)}</dd></div>
    </dl>
    <section className="detail-block workflow-panel"><h3>Workflow</h3><div className="next-actions">{data.workflow?.allowed_next?.length ? data.workflow.allowed_next.map((status) => <button key={status} className="button compact" onClick={() => run(() => api.applications.transition(applicationId, status), `Moved to ${labelize(status)}`)}>Move to {labelize(status)}</button>) : <span className="muted">No standard transition is currently available.</span>}</div></section>
    <ApplicationActions application={data} run={run} />
    <Documents application={data} run={run} />
    <section className="detail-block"><h3>Timeline</h3><ul className="timeline">{timeline?.timeline?.length ? timeline.timeline.map((item, index) => <li key={`${item.type}-${index}`}><strong>{labelize(item.type)}</strong><br /><span className="muted">{formatDate(item.at)}</span></li>) : <li>No events recorded.</li>}</ul></section>
  </>}</Modal>;
}

function ApplicationActions({ application, run }) {
  const submit = (event) => {
    event.preventDefault();
    const raw = formObject(event.currentTarget); const id = application.application_id;
    if (raw.action === "certificate") return run(() => api.applications.action(id, "certificate"), "Certificate issued");
    if (raw.action === "missing-documents") return run(() => api.applications.action(id, raw.action, { documents: splitList(raw.value) }), "Missing documents recorded");
    if (raw.action === "notes") return run(() => api.applications.action(id, raw.action, { note: raw.value, visibility: "staff_only" }), "Note added");
    return run(() => api.applications.action(id, raw.action, { reason: raw.value }), `${labelize(raw.action)} recorded`);
  };
  return <section className="detail-block"><h3>Actions</h3><form className="inline-action" onSubmit={submit}><select name="action" defaultValue="notes"><option value="notes">Add note</option><option value="missing-documents">Request missing documents</option><option value="hold">Place on hold</option><option value="objection">Record objection</option><option value="reject">Reject application</option><option value="certificate">Issue certificate</option></select><input name="value" placeholder="Reason, note, or comma-separated documents" /><button className="button secondary compact">Apply</button></form></section>;
}

function Documents({ application, run }) {
  const upload = (event) => {
    event.preventDefault(); const raw = formObject(event.currentTarget);
    run(() => api.applications.uploadDocument(application.application_id, { document_type: raw.document_type, file_name: raw.file_name, uploaded_by_applicant_id: application.applicant_ref?.applicant_id }), "Document metadata uploaded");
    event.currentTarget.reset();
  };
  return <section className="detail-block"><h3>Documents</h3><div className="document-list">{application.required_documents?.map((doc) => <div className="document-row" key={doc.document_id}><span><strong>{labelize(doc.document_type)}</strong><small>{doc.file_name || "Not uploaded"}</small></span><StatusPill status={doc.status} /><div className="button-row"><button className="button secondary compact" onClick={() => run(() => api.applications.reviewDocument(application.application_id, doc.document_id, { status: "verified" }), "Document verified")}>Verify</button><button className="button secondary compact" onClick={() => run(() => api.applications.reviewDocument(application.application_id, doc.document_id, { status: "rejected" }), "Document rejected")}>Reject</button></div></div>)}</div><form className="inline-action" onSubmit={upload}><input name="document_type" placeholder="Document type" required /><input name="file_name" placeholder="File name or reference" required /><button className="button secondary compact">Upload metadata</button></form></section>;
}
