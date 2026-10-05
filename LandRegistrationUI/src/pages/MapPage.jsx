import L from "leaflet";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import { APPLICATION_STATUSES, APPLICATION_TYPES } from "../constants";
import { ErrorState, Loading } from "../components/AsyncState";
import { escapeHtml, labelize } from "../utils";

export default function MapPage() {
  const [zone, setZone] = useState(""); const [status, setStatus] = useState(""); const [type, setType] = useState("");
  const [feed, setFeed] = useState(null); const [error, setError] = useState(null); const [refresh, setRefresh] = useState(0);
  const load = useCallback(() => { setError(null); api.analytics.parcels({ zone_id: zone, status, application_type: type, limit: 1000 }).then(setFeed).catch(setError); }, [zone, status, type]);
  useEffect(() => { load(); }, [load, refresh]);
  return <section className="page-grid"><article className="page-section span-9"><div className="section-header"><div><h2>Live parcel map</h2><p>GeoJSON parcel locations returned by the backend.</p></div></div><div className="section-body">{error ? <ErrorState error={error} retry={() => setRefresh((value) => value + 1)} /> : !feed ? <Loading label="Loading map data…" /> : <LeafletMap feed={feed} />}</div></article><article className="page-section span-3"><div className="section-header"><div><h2>Map filters</h2><p>Up to 1,000 matching locations.</p></div></div><div className="section-body filter-stack"><label>Zone<input value={zone} onChange={(event) => setZone(event.target.value)} placeholder="ZONE-RM-01" /></label><label>Status<select value={status} onChange={(event) => setStatus(event.target.value)}><option value="">All statuses</option>{APPLICATION_STATUSES.map((value) => <option key={value} value={value}>{labelize(value)}</option>)}</select></label><label>Application type<select value={type} onChange={(event) => setType(event.target.value)}><option value="">All types</option>{APPLICATION_TYPES.map((value) => <option key={value} value={value}>{labelize(value)}</option>)}</select></label><div className="zone-row"><span>Visible applications</span><strong>{feed?.features?.length || 0}</strong></div></div></article></section>;
}

function LeafletMap({ feed }) {
  const nodeRef = useRef(null);
  useEffect(() => {
    const map = L.map(nodeRef.current).setView([31.9, 35.2], 8);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "&copy; OpenStreetMap contributors" }).addTo(map);
    const layer = L.geoJSON(feed, {
      pointToLayer: (_, latlng) => L.circleMarker(latlng, { radius: 9, color: "#176b5d", fillColor: "#b56b2a", fillOpacity: 0.75, weight: 2 }),
      style: { color: "#176b5d", fillColor: "#b56b2a", fillOpacity: 0.35, weight: 2 },
      onEachFeature: (feature, item) => { const p = feature.properties; item.bindPopup(`<strong>${escapeHtml(p.application_id)}</strong><br>${escapeHtml(labelize(p.application_type))}<br>${escapeHtml(labelize(p.status))}<br>Parcel ${escapeHtml(p.parcel_number)} · ${escapeHtml(p.zone_id)}`); },
    }).addTo(map);
    if (layer.getLayers().length) map.fitBounds(layer.getBounds().pad(0.15), { maxZoom: 15 });
    return () => map.remove();
  }, [feed]);
  return <div ref={nodeRef} className="map-panel" aria-label="Application parcel map" />;
}
