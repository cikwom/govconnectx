export type UserRole = "citizen" | "official" | "department_admin" | "supervisor" | "system_admin";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  department_id?: number | null;
  is_active: boolean;
  home_state_code?: string | null;
  home_lga_code?: string | null;
}

export interface GeographicState {
  code: string;
  name: string;
  geopolitical_zone: string;
}

export interface LocalGovernmentArea {
  code: string;
  name: string;
  state_code: string;
}
export interface GeographicWard { code: string; name: string; lga_code: string }
export interface Community { code: string; name: string; ward_code: string }

export interface AuthResponse { access_token: string; token_type: string; user: User }
export interface Report {
  id: number;
  title: string;
  description: string;
  category: string;
  latitude: number;
  longitude: number;
  gps_latitude?: number | null;
  gps_longitude?: number | null;
  location_review_status?: "not_provided" | "pending" | "verified" | "mismatch" | "unable_to_verify";
  location_reviewed_by_user_id?: number | null;
  location_reviewed_at?: string | null;
  location_review_note?: string | null;
  address: string | null;
  incident_state_code?: string | null;
  incident_lga_code?: string | null;
  incident_ward_code?: string | null;
  incident_community_code?: string | null;
  department_id?: number | null;
  status: string;
  sla_due_at: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
}
export interface RegisterPayload {
  email: string;
  full_name: string;
  password: string;
  home_state_code: string;
  home_lga_code: string;
}
export interface CreateReportPayload {
  title: string;
  description: string;
  category: string;
  latitude: number;
  longitude: number;
  gps_latitude?: number;
  gps_longitude?: number;
  address?: string;
  incident_state_code: string;
  incident_lga_code: string;
  incident_ward_code?: string;
  incident_community_code?: string;
}
export interface HistoryItem { id: number; report_id: number; changed_by_user_id: number; old_status: string | null; new_status: string; message: string | null; is_public: boolean; created_at: string }
export interface CommentItem { id: number; report_id: number; author_user_id: number; body: string; is_internal: boolean; created_at: string }
export interface ReportAttachment { id: number; report_id: number; uploaded_by_user_id: number; original_filename: string; content_type: string; size_bytes: number; sha256: string; created_at: string }
