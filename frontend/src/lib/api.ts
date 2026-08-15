/** Mizizi API client. */

import type {
  AuthResponse,
  Community,
  CreatedObject,
  CulturalObject,
  Derivative,
  Language,
  ObjectType,
  PaginatedObjects,
  Permission,
  Place,
  PublishCheck,
  RegisterPayload,
  ReviewerApplication,
  SearchResponse,
  User,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export const TOKEN_KEY = "mizizi:token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  getToken,
  setToken,
  clearToken,

  // Reference data
  languages: () => request<Language[]>("/languages"),
  communities: () => request<Community[]>("/communities"),
  places: () => request<Place[]>("/places"),

  // Auth
  auth: {
    register: (payload: RegisterPayload) =>
      request<AuthResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    login: (email: string, password: string) =>
      request<AuthResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    me: () => request<User>("/auth/me"),
    logout: () =>
      request<{ ok: boolean }>("/auth/logout", { method: "POST" }),
    myObjects: () => request<CulturalObject[]>("/auth/me/objects"),
    applyReviewer: (statement: string) =>
      request<ReviewerApplication>("/auth/apply-reviewer", {
        method: "POST",
        body: JSON.stringify({ statement }),
      }),
    listApplications: () => request<ReviewerApplication[]>("/auth/reviewer-applications"),
    decideApplication: (id: string, approve: boolean) =>
      request<ReviewerApplication>(`/auth/reviewer-applications/${id}/decide`, {
        method: "POST",
        body: JSON.stringify({ approve }),
      }),
  },

  // Cultural objects
  listObjects: (params: Record<string, string | number | undefined> = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined) as [string, string][]
    ).toString();
    return request<PaginatedObjects>(`/cultural-objects${qs ? `?${qs}` : ""}`);
  },
  getObject: (id: string) => request<CulturalObject>(`/cultural-objects/${id}`),
  updateObject: (
    id: string,
    payload: {
      title?: string;
      description?: string;
      original_language_id?: string;
      community_id?: string;
      place_id?: string;
    }
  ) =>
    request<CulturalObject>(`/cultural-objects/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  createObject: (payload: {
    object_type: ObjectType;
    title?: string;
    description?: string;
    original_language_id?: string;
    community_id?: string;
    place_id?: string;
  }) =>
    request<CreatedObject>("/cultural-objects", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  uploadMedia: async (objectId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    const token = getToken();
    const res = await fetch(`${API_BASE}/cultural-objects/${objectId}/media`, {
      method: "POST",
      body: form,
      ...(token ? { headers: { Authorization: `Bearer ${token}` } } : {}),
    });
    if (!res.ok) throw new Error(`Upload failed (${res.status})`);
    return res.json();
  },
  setPermissions: (
    objectId: string,
    payload: Partial<Record<string, boolean>>,
    creatorKey?: string
  ) =>
    request<Permission>(`/cultural-objects/${objectId}/permissions`, {
      method: "PUT",
      body: JSON.stringify(payload),
      ...(creatorKey ? { headers: { "X-Creator-Key": creatorKey } } : {}),
    }),
  createTranscription: (
    objectId: string,
    payload: { text: string; language_id?: string; verification_status?: string }
  ) =>
    request(`/cultural-objects/${objectId}/transcriptions`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createTranslation: (
    objectId: string,
    payload: { text: string; source_language_id?: string; target_language_id?: string }
  ) =>
    request(`/cultural-objects/${objectId}/translations`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createConsent: (objectId: string, payload: { consenting_party: string; consent_type: string }) =>
    request(`/cultural-objects/${objectId}/consents`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createDerivative: (
    objectId: string,
    payload: { derivative_type: string; title?: string; content?: string; model_name?: string }
  ) =>
    request<Derivative>(`/cultural-objects/${objectId}/derivatives`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  setStatus: (objectId: string, status: string) =>
    request(`/cultural-objects/${objectId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  publish: (objectId: string) =>
    request<CulturalObject>(`/cultural-objects/${objectId}/publish`, { method: "POST" }),
  publishCheck: (objectId: string) =>
    request<PublishCheck>(
      `/cultural-objects/${objectId}/publish-check`
    ),
  withdraw: (objectId: string) => request(`/cultural-objects/${objectId}`, { method: "DELETE" }),

  // Search
  search: (q: string) => request<SearchResponse>(`/search?q=${encodeURIComponent(q)}`),
};