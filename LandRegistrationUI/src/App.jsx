import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import { ROUTES } from "./constants";
import { Loading } from "./components/AsyncState";

const pages = {
  dashboard: lazy(() => import("./pages/DashboardPage")),
  applications: lazy(() => import("./pages/ApplicationsPage")),
  applicants: lazy(() => import("./pages/ApplicantsPage")),
  staff: lazy(() => import("./pages/StaffPage")),
  assignments: lazy(() => import("./pages/AssignmentsPage")),
  analytics: lazy(() => import("./pages/AnalyticsPage")),
  maps: lazy(() => import("./pages/MapPage")),
};

function currentRoute() {
  const route = window.location.hash.slice(1);
  return pages[route] ? route : "dashboard";
}

export default function App() {
  const [route, setRoute] = useState(currentRoute);
  const [navOpen, setNavOpen] = useState(false);
  const [toast, setToast] = useState(null);
  useEffect(() => {
    const update = () => { setRoute(currentRoute()); setNavOpen(false); };
    window.addEventListener("hashchange", update);
    if (!window.location.hash) window.location.hash = "dashboard";
    return () => window.removeEventListener("hashchange", update);
  }, []);
  useEffect(() => {
    if (!toast) return undefined;
    const timer = setTimeout(() => setToast(null), 4200);
    return () => clearTimeout(timer);
  }, [toast]);
  const notify = useCallback((message, type = "success") => setToast({ message, type, key: Date.now() }), []);
  const Page = pages[route];
  const title = ROUTES.find(([id]) => id === route)?.[1] || "Dashboard";
  return <div className={navOpen ? "nav-open" : ""}>
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#dashboard" aria-label="LRMIS dashboard"><span className="brand-mark">LR</span><span><strong>LRMIS</strong><small>Land Registration</small></span></a>
        <nav className="nav" aria-label="Primary navigation">{ROUTES.map(([id, label, icon]) => <a key={id} href={`#${id}`} className={id === route ? "active" : ""}><span className="nav-icon">{icon}</span><span>{label}</span></a>)}</nav>
      </aside>
      <div className="main-shell">
        <header className="topbar"><button className="icon-button" type="button" onClick={() => setNavOpen((value) => !value)} aria-label="Toggle navigation"><span /><span /><span /></button><div><p className="eyebrow">LRMIS</p><h1>{title}</h1></div></header>
        <main className="page-content"><Suspense fallback={<Loading />}><Page notify={notify} /></Suspense></main>
      </div>
    </div>
    {toast && <div className="toast-root" aria-live="polite"><div key={toast.key} className={`toast ${toast.type}`}>{toast.message}</div></div>}
  </div>;
}
