import type {
  AuthResponse, CommentItem, CreateReportPayload, GeographicState, HistoryItem,
  Community, GeographicWard, LocalGovernmentArea, RegisterPayload, Report, ReportAttachment, User,
} from "../types/api";

const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
const TOKEN_KEY = "govconnectx_access_token";

type CommunityListing = { id: number; listing_type: "lost" | "found"; title: string; description: string; location_text: string; contact_instructions: string; created_at: string };
type ServiceDirectoryEntry = { id: number; name: string; category: string; description: string; address: string; phone: string | null; website: string | null; is_verified: boolean };
type AdminCommunityListing = CommunityListing & { moderation_status: string };
type Preferences = { email_notifications: boolean; in_app_notifications: boolean; sms_notifications: boolean; sms_consent_at: string | null; sms_consent_revoked_at: string | null; phone_number: string | null; phone_verified_at: string | null; preferred_language: "en" | "ha" | "yo" | "ig"; updated_at: string };
type Department = { id: number; name: string; description: string | null; is_active: boolean; created_at: string };
type DepartmentMember = { id: number; full_name: string; role: string };
type DepartmentPerformance = { department_id: number; scope: string; total_reports: number; open_reports: number; resolved_reports: number; overdue_reports: number; resolution_rate_percent: number; average_resolution_hours: number | null; status_counts: Record<string, number>; measurement_note: string };

type NotificationDeliverySummary = { by_status: Record<string, number>; by_channel: Record<string, number>; queued: number; sending: number; sent: number; failed: number };
type NotificationDeliveryItem = { id: number; channel: "email" | "sms"; destination: string; status: "queued" | "sending" | "sent" | "failed"; attempts: number; max_attempts: number; next_attempt_at: string | null; last_error: string | null; created_at: string | null; sent_at: string | null };
type NotificationDeliveryReport = { summary: NotificationDeliverySummary; items: NotificationDeliveryItem[] };

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const token = tokenStore.get();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_URL}/api/v1${path}`, { ...options, headers });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    } catch { /* Keep the status-based message. */ }
    if (response.status === 401) tokenStore.clear();
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

async function requestBlob(path: string): Promise<Blob> {
  const headers = new Headers();
  const token = tokenStore.get();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_URL}/api/v1${path}`, { headers });
  if (!response.ok) {
    let message = `Download failed (${response.status})`;
    try { const body = await response.json(); message = body.detail ?? message; } catch { /* Keep fallback. */ }
    if (response.status === 401) tokenStore.clear();
    throw new Error(message);
  }
  return response.blob();
}

export const api = {
  states: () => request<GeographicState[]>("/locations/states"),
  lgas: (stateCode: string) => request<LocalGovernmentArea[]>(`/locations/states/${encodeURIComponent(stateCode)}/lgas`),
  wards: (lgaCode: string) => request<GeographicWard[]>(`/locations/lgas/${encodeURIComponent(lgaCode)}/wards`),
  communities: (wardCode: string) => request<Community[]>(`/locations/wards/${encodeURIComponent(wardCode)}/communities`),
  createWard: (payload: { code: string; name: string; lga_code: string }) => request<GeographicWard>("/locations/admin/wards", { method: "POST", body: JSON.stringify(payload) }),
  createCommunity: (payload: { code: string; name: string; ward_code: string }) => request<Community>("/locations/admin/communities", { method: "POST", body: JSON.stringify(payload) }),
  register: (p: RegisterPayload) => request<User>("/auth/register", { method: "POST", body: JSON.stringify(p) }),
  login: (email: string, password: string) => request<AuthResponse>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: () => request<User>("/auth/me"),
  reports: () => request<Report[]>("/reports"),
  report: (id: number) => request<Report>(`/reports/${id}`),
  createReport: (p: CreateReportPayload) => request<Report>("/reports", { method: "POST", body: JSON.stringify(p) }),
  reportHistory: (id: number) => request<HistoryItem[]>(`/reports/${id}/history`),
  reportComments: (id: number) => request<CommentItem[]>(`/reports/${id}/comments`),
  addReportComment: (id: number, body: string) => request<CommentItem>(`/reports/${id}/comments`, { method: "POST", body: JSON.stringify({ body, is_internal: false }) }),
  reportAttachments: (id: number) => request<ReportAttachment[]>(`/reports/${id}/attachments`),
  uploadReportAttachment: (id: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<ReportAttachment>(`/reports/${id}/attachments`, { method: "POST", body: form });
  },
  downloadReportAttachment: (reportId: number, attachmentId: number) => requestBlob(`/reports/${reportId}/attachments/${attachmentId}/download`),

  duplicateHint: (id: number) => request<{ possible_duplicate_count: number; review_recommended: boolean; message: string }>(`/reports/${id}/duplicate-hint`),
  requestEscalation: (id: number, urgency: "normal" | "high" | "critical", reason: string) => request<{ id: number; status: string; notice: string }>(`/reports/${id}/escalations`, { method: "POST", body: JSON.stringify({ urgency, reason }) }),
  submitReportFeedback: (id: number, rating: number, comment?: string) => request<{ id: number; report_id: number; rating: number; comment: string | null }>(`/reports/${id}/feedback`, { method: "POST", body: JSON.stringify({ rating, comment }) }),
  communityListings: () => request<CommunityListing[]>("/community/listings"),
  createCommunityListing: (payload: { listing_type: "lost" | "found"; title: string; description: string; location_text: string; contact_instructions: string }) => request<CommunityListing>("/community/listings", { method: "POST", body: JSON.stringify(payload) }),
  publicServiceDirectory: () => request<ServiceDirectoryEntry[]>("/service-directory"),
  adminCommunityListings: () => request<AdminCommunityListing[]>("/admin/community/listings"),
  moderateCommunityListing: (id: number, moderation_status: "APPROVED" | "REJECTED") => request<{ id: number; moderation_status: string }>(`/admin/community/listings/${id}`, { method: "PATCH", body: JSON.stringify({ moderation_status }) }),
  createServiceDirectoryEntry: (payload: { name: string; category: string; description: string; address: string; phone?: string }) => request<ServiceDirectoryEntry>("/admin/service-directory", { method: "POST", body: JSON.stringify(payload) }),
  adminNotificationDeliveries: () => request<NotificationDeliveryReport>("/admin/notification-deliveries"),
  preferences: () => request<Preferences>("/preferences"),
  updatePreferences: (payload: Pick<Preferences, "email_notifications" | "in_app_notifications" | "sms_notifications" | "preferred_language">) => request<Preferences>("/preferences", { method: "PUT", body: JSON.stringify(payload) }),
  requestPhoneVerification: (phone_number: string) => request<{ message: string }>("/preferences/phone/request-verification", { method: "POST", body: JSON.stringify({ phone_number }) }),
  verifyPhone: (code: string) => request<{ message: string }>("/preferences/phone/verify", { method: "POST", body: JSON.stringify({ code }) }),
  departmentPerformance: () => request<DepartmentPerformance>("/departments/me/performance"),
  departments: () => request<Department[]>("/departments"),
  departmentMembers: (departmentId: number) => request<DepartmentMember[]>(`/departments/${departmentId}/members`),
  assignReport: (reportId: number, departmentId: number, assignedToUserId: number | null, note?: string) => request(`/reports/${reportId}/assignments`, { method: "POST", body: JSON.stringify({ department_id: departmentId, assigned_to_user_id: assignedToUserId, note }) }),
  updateReportStatus: (reportId: number, nextStatus: string, message?: string) => request<Report>(`/reports/${reportId}/status`, { method: "PATCH", body: JSON.stringify({ status: nextStatus, message }) }),
};
