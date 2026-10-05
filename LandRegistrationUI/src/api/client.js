const API_URL = (import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message, status, details) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export async function request(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      signal: controller.signal,
      headers: { Accept: "application/json", ...(options.body ? { "Content-Type": "application/json" } : {}), ...options.headers },
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = data?.detail;
      const message = Array.isArray(detail) ? detail.map((item) => item.msg).join(", ") : detail || data?.message || `Request failed (${response.status})`;
      throw new ApiError(message, response.status, data);
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw new ApiError("The request timed out. Check the API connection.", 408);
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export function queryString(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.set(key, String(value));
  });
  const value = query.toString();
  return value ? `?${value}` : "";
}

export const api = {
  applications: {
    list: (params) => request(`/applications/${queryString(params)}`),
    get: (id) => request(`/applications/${encodeURIComponent(id)}`),
    create: (body, key) => request("/applications/", { method: "POST", headers: key ? { "Idempotency-Key": key } : {}, body }),
    transition: (id, newStatus) => request(`/applications/${encodeURIComponent(id)}/transition`, { method: "PATCH", body: { new_status: newStatus } }),
    action: (id, action, body) => request(`/applications/${encodeURIComponent(id)}/${action}`, { method: "POST", body }),
    reviewDocument: (id, documentId, body) => request(`/applications/${encodeURIComponent(id)}/documents/${documentId}`, { method: "PATCH", body }),
    uploadDocument: (id, body) => request(`/applications/${encodeURIComponent(id)}/documents`, { method: "POST", body }),
    timeline: (id) => request(`/applications/${encodeURIComponent(id)}/timeline`),
  },
  applicants: {
    list: (params) => request(`/applicants/${queryString(params)}`),
    get: (id) => request(`/applicants/${encodeURIComponent(id)}`),
    create: (body) => request("/applicants/", { method: "POST", body }),
    applications: (id, params = {}) => request(`/applicants/${encodeURIComponent(id)}/applications${queryString(params)}`),
  },
  staff: {
    list: (params) => request(`/staff/${queryString(params)}`),
    get: (id) => request(`/staff/${encodeURIComponent(id)}`),
    create: (body) => request("/staff/", { method: "POST", body }),
  },
  assignments: {
    list: (params) => request(`/survey-tasks/${queryString(params)}`),
    autoAssign: (id) => request(`/applications/${encodeURIComponent(id)}/auto-assign-surveyor`, { method: "POST" }),
    milestone: (id, body) => request(`/applications/${encodeURIComponent(id)}/survey-milestone`, { method: "PATCH", body }),
    report: (id, body) => request(`/applications/${encodeURIComponent(id)}/survey-report`, { method: "POST", body }),
    review: (id, body) => request(`/applications/${encodeURIComponent(id)}/registrar-review`, { method: "PATCH", body }),
  },
  analytics: {
    kpis: () => request("/analytics/kpis"),
    status: () => request("/analytics/applications-by-status"),
    types: () => request("/analytics/applications-by-type"),
    zones: () => request("/analytics/applications-by-zone"),
    processing: () => request("/analytics/processing-time"),
    surveyors: () => request("/analytics/surveyors"),
    parcels: (params) => request(`/analytics/geofeeds/parcels${queryString(params)}`),
  },
};
