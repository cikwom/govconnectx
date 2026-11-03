export type UserRole = "citizen" | "official" | "department_admin" | "supervisor" | "system_admin";
export interface User { id:number; email:string; full_name:string; role:UserRole; is_active:boolean; }
export interface AuthResponse { access_token:string; token_type:string; user:User; }
export interface Report { id:number; title:string; description:string; category:string; latitude:number; longitude:number; address:string|null; status:string; sla_due_at:string|null; resolved_at:string|null; created_at:string; updated_at:string; }
export interface RegisterPayload { email:string; full_name:string; password:string; }
export interface CreateReportPayload { title:string; description:string; category:string; latitude:number; longitude:number; address?:string; }
