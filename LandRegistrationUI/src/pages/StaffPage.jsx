import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { ErrorState, Loading } from "../components/AsyncState";
import Field from "../components/Field";
import Modal from "../components/Modal";
import Pagination from "../components/Pagination";
import StatusPill from "../components/StatusPill";
import Table from "../components/Table";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { formatDate, labelize, splitList } from "../utils";

const formObject = (form) => Object.fromEntries(new FormData(form).entries());

export default function StaffPage({ notify }) {
  const [search, setSearch] = useState(""); const [role, setRole] = useState(""); const [page, setPage] = useState(1);
  const [result, setResult] = useState(null); const [error, setError] = useState(null); const [createOpen, setCreateOpen] = useState(false); const [refresh, setRefresh] = useState(0);
  const debounced = useDebouncedValue(search);
  const load = useCallback(() => { setError(null); api.staff.list({ search: debounced, role, page, page_size: 20 }).then(setResult).catch(setError); }, [debounced, role, page]);
  useEffect(() => { load(); }, [load, refresh]);
  return <><section className="page-section"><div className="section-header"><div><h2>Staff directory</h2><p>Surveyors, registrars, coverage, and current workload.</p></div><button className="button" onClick={() => setCreateOpen(true)}>New staff member</button></div>
    <div className="section-body"><div className="filters"><input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="Search code, name, or email" /><select value={role} onChange={(event) => { setRole(event.target.value); setPage(1); }}><option value="">All roles</option><option value="surveyor">Surveyor</option><option value="registrar">Registrar</option><option value="officer">Officer</option></select></div></div>
    <div className="section-body">{error ? <ErrorState error={error} retry={load} /> : !result ? <Loading /> : <><Table rows={result.items} empty="No staff records found." columns={[{ label: "Code", key: "staff_code" }, { label: "Name", key: "name" }, { label: "Role", render: (row) => labelize(row.role) }, { label: "Zones", render: (row) => row.coverage?.zone_ids?.join(", ") || "—" }, { label: "Workload", render: (row) => `${row.workload?.active_tasks || 0} / ${row.workload?.max_tasks || 0}` }, { label: "Status", render: (row) => <StatusPill status={row.active ? "active" : "inactive"} /> }, { label: "Created", render: (row) => formatDate(row.created_at) }]} /><Pagination page={result.page} pages={result.pages} total={result.total} onChange={setPage} /></>}</div>
  </section>{createOpen && <CreateStaff onClose={() => setCreateOpen(false)} notify={notify} onCreated={() => { setCreateOpen(false); notify("Staff member created"); setRefresh((value) => value + 1); }} />}</>;
}

function CreateStaff({ onClose, onCreated, notify }) {
  const [saving, setSaving] = useState(false);
  const submit = async (event) => { event.preventDefault(); setSaving(true); const raw = formObject(event.currentTarget); try { await api.staff.create({ staff_code: raw.staff_code, name: raw.name, role: raw.role, department: raw.department, skills: splitList(raw.skills), contacts: { email: raw.email, phone: raw.phone }, coverage: { zone_ids: splitList(raw.zone_ids) }, workload: { active_tasks: 0, max_tasks: Number(raw.max_tasks) }, active: true }); onCreated(); } catch (error) { notify(error.message, "error"); setSaving(false); } };
  return <Modal title="Create staff member" onClose={onClose}><form className="form-grid" onSubmit={submit}><Field label="Staff code" name="staff_code" required /><Field label="Name" name="name" required /><Field label="Role" name="role" options={["surveyor", "registrar", "officer"]} /><Field label="Department" name="department" required /><Field label="Email" name="email" type="email" required /><Field label="Phone" name="phone" required /><Field label="Skills" name="skills" placeholder="Comma-separated" /><Field label="Coverage zones" name="zone_ids" placeholder="Comma-separated" required /><Field label="Maximum active tasks" name="max_tasks" type="number" min="1" defaultValue="10" /><div className="form-field full"><button className="button" disabled={saving}>{saving ? "Creating…" : "Create staff"}</button></div></form></Modal>;
}
