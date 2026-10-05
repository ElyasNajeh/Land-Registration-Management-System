import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { APPLICANT_TYPES } from "../constants";
import { ErrorState, Loading } from "../components/AsyncState";
import Field from "../components/Field";
import Modal from "../components/Modal";
import Pagination from "../components/Pagination";
import StatusPill from "../components/StatusPill";
import Table from "../components/Table";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { formatDate, labelize } from "../utils";

const formObject = (form) => Object.fromEntries(new FormData(form).entries());

export default function ApplicantsPage({ notify }) {
  const [search, setSearch] = useState("");
  const [type, setType] = useState("");
  const [page, setPage] = useState(1);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [selected, setSelected] = useState(null);
  const [refresh, setRefresh] = useState(0);
  const debounced = useDebouncedValue(search);
  const load = useCallback(() => {
    setError(null);
    api.applicants.list({ search: debounced, applicant_type: type, page, page_size: 20 }).then(setResult).catch(setError);
  }, [debounced, type, page]);
  useEffect(() => { load(); }, [load, refresh]);
  return <>
    <section className="page-section"><div className="section-header"><div><h2>Applicant profiles</h2><p>Search by name, national ID, or email.</p></div><button className="button" onClick={() => setCreateOpen(true)}>New applicant</button></div>
      <div className="section-body"><div className="filters"><input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="Search applicants" /><select value={type} onChange={(event) => { setType(event.target.value); setPage(1); }}><option value="">All applicant types</option>{APPLICANT_TYPES.map((value) => <option key={value} value={value}>{labelize(value)}</option>)}</select></div></div>
      <div className="section-body">{error ? <ErrorState error={error} retry={load} /> : !result ? <Loading /> : <><Table rows={result.items} empty="No applicants found." columns={[
        { label: "Applicant", render: (row) => <button className="link-button" onClick={() => setSelected(row._id)}>{row.full_name}</button> },
        { label: "Type", render: (row) => labelize(row.applicant_type) }, { label: "Email", render: (row) => row.contacts?.email },
        { label: "Verification", render: (row) => <StatusPill status={row.identity?.verification_state || "unverified"} /> },
        { label: "Applications", render: (row) => row.stats?.total_applications || 0 }, { label: "Created", render: (row) => formatDate(row.created_at) },
      ]} /><Pagination page={result.page} pages={result.pages} total={result.total} onChange={setPage} /></>}</div>
    </section>
    {createOpen && <CreateApplicant onClose={() => setCreateOpen(false)} onCreated={(applicant) => { setCreateOpen(false); notify(`Applicant ${applicant.full_name} created`); setSelected(applicant._id); setRefresh((value) => value + 1); }} notify={notify} />}
    {selected && <ApplicantDetail applicantId={selected} onClose={() => setSelected(null)} />}
  </>;
}

function CreateApplicant({ onClose, onCreated, notify }) {
  const [saving, setSaving] = useState(false);
  const submit = async (event) => {
    event.preventDefault(); setSaving(true); const raw = formObject(event.currentTarget);
    try {
      onCreated(await api.applicants.create({ full_name: raw.full_name, applicant_type: raw.applicant_type, national_id: raw.national_id, contacts: { email: raw.email, phone: raw.phone }, address: { city: raw.city, street: raw.street || null, zone_id: raw.zone_id || null }, preferences: { preferred_contact: raw.preferred_contact, language: raw.language, notifications: { on_status_change: true, on_missing_documents: true, on_certificate_ready: true } } }));
    } catch (error) { notify(error.message, "error"); setSaving(false); }
  };
  return <Modal title="Create applicant" onClose={onClose}><form className="form-grid" onSubmit={submit}>
    <Field label="Full name" name="full_name" required /><Field label="Applicant type" name="applicant_type" options={APPLICANT_TYPES} required />
    <Field label="National ID / registration no." name="national_id" required /><Field label="Email" name="email" type="email" required />
    <Field label="Phone" name="phone" required /><Field label="City" name="city" required /><Field label="Street" name="street" /><Field label="Zone" name="zone_id" />
    <Field label="Preferred contact" name="preferred_contact" options={["email", "phone"]} /><Field label="Language" name="language" options={[{ value: "ar", label: "Arabic" }, { value: "en", label: "English" }]} />
    <div className="form-field full"><button className="button" disabled={saving}>{saving ? "Creating…" : "Create applicant"}</button></div>
  </form></Modal>;
}

function ApplicantDetail({ applicantId, onClose }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => {
    Promise.all([api.applicants.get(applicantId), api.applicants.applications(applicantId, { page_size: 20 })]).then(([profile, applications]) => setData({ profile, applications })).catch(setError);
  }, [applicantId]);
  return <Modal title="Applicant details" onClose={onClose} wide>{error ? <ErrorState error={error} /> : !data ? <Loading /> : <>
    <div className="section-header compact-header"><div><h2>{data.profile.full_name}</h2><p>{labelize(data.profile.applicant_type)} · {data.profile._id}</p></div><StatusPill status={data.profile.identity?.verification_state} /></div>
    <dl className="detail-list"><div><dt>Email</dt><dd>{data.profile.contacts?.email}</dd></div><div><dt>Phone</dt><dd>{data.profile.contacts?.phone}</dd></div><div><dt>Address</dt><dd>{[data.profile.address?.city, data.profile.address?.street].filter(Boolean).join(", ")}</dd></div><div><dt>Created</dt><dd>{formatDate(data.profile.created_at)}</dd></div></dl>
    <div className="detail-block"><h3>Applications</h3><Table rows={data.applications.items} empty="No linked applications." columns={[{ label: "Application", key: "application_id" }, { label: "Type", render: (row) => labelize(row.application_type) }, { label: "Status", render: (row) => <StatusPill status={row.status} /> }, { label: "Zone", render: (row) => row.parcel_ref?.zone_id }]} /></div>
  </>}</Modal>;
}
