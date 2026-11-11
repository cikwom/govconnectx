import { useCallback, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { tokenStore } from "../services/api";
import { useAuth } from "../state/AuthContext";
import GeographicOperationsPanel from "../components/GeographicOperationsPanel";
import AuditLogPanel from "../components/AuditLogPanel";
import CommunityModerationPanel from "../components/CommunityModerationPanel";
import GeographicDirectoryPanel from "../components/GeographicDirectoryPanel";
import GeographicBulkImportPanel from "../components/GeographicBulkImportPanel";
import { useLanguage } from "../state/LanguageContext";

type Overview = {
  users: { total: number; active: number; inactive: number; by_role: Record<string, number>; registered_today: number };
  reports: { total: number; by_status: Record<string, number>; open: number; overdue: number };
};
type AdminUser = { id: number; full_name: string; email: string; role: string; is_active: boolean; created_at: string | null; reports_submitted: number };
type Activity = { id: string; type: string; actor: string; actor_role: string; description: string; report_id: number | null; created_at: string | null };
type AdminReport = { id: number; title: string; description: string; category: string; status: string; address: string | null; created_at: string | null; reporter: { id: number; full_name: string; email: string } | null };
type LocationReview = { id:number; title:string; category:string; gps_latitude:number; gps_longitude:number; incident_state_code:string|null; incident_lga_code:string|null; address:string|null; location_review_status:string; created_at:string|null };
type OversightSignal = { code: string; label: string; detail: string };
type OversightItem = {
  user: { id: number; full_name: string; email: string; is_active: boolean };
  review_priority: "medium" | "high";
  reports_in_window: number;
  max_reports_in_24h: number;
  signals: OversightSignal[];
  reports: { id: number; title: string; category: string; status: string; address: string | null; created_at: string | null }[];
};
type Oversight = {
  window_days: number;
  thresholds: { min_reports: number; burst_threshold: number; burst_window_hours: number };
  summary: { citizens_reviewed: number; flagged_citizens: number; high_priority: number; reports_analyzed: number };
  items: OversightItem[];
  notice: string;
};
const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(new RegExp("/$"), "");
async function adminRequest<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}/api/v1/admin${path}`, { headers: { Authorization: `Bearer ${tokenStore.get() ?? ""}` } });
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail ?? `Request failed (${response.status})`); }
  return response.json() as Promise<T>;
}
const dateTime = (value: string | null, locale: string) => value ? new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "—";

export default function AdminDashboardPage() {
  const { user } = useAuth();
  const { t, locale } = useLanguage();
  const [overview, setOverview] = useState<Overview | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [reports, setReports] = useState<AdminReport[]>([]);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [oversight, setOversight] = useState<Oversight | null>(null);
  const [locationReviews, setLocationReviews] = useState<LocationReview[]>([]);
  const [search, setSearch] = useState("");
  const [reportSearch, setReportSearch] = useState("");
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [filterBusy, setFilterBusy] = useState(false);

  const load = useCallback(async () => {
    setError("");
    try {
      const [summary, people, reportList, events, patterns, gpsReviews] = await Promise.all([
        adminRequest<Overview>("/overview"),
        adminRequest<{ items: AdminUser[] }>("/users?limit=100"),
        adminRequest<{ items: AdminReport[] }>("/reports?limit=100"),
        adminRequest<Activity[]>("/activity?limit=35"),
        adminRequest<Oversight>("/oversight?window_days=30"),
        adminRequest<{items:LocationReview[]}>("/reports/location-review?status=pending"),
      ]);
      setOverview(summary);
      setUsers(people.items);
      setReports(reportList.items);
      setActivity(events);
      setOversight(patterns);
      setLocationReviews(gpsReviews.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("Could not load admin data"));
    } finally {
      setBusy(false);
      setFilterBusy(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);
  if (user && user.role !== "system_admin") return <Navigate to="/dashboard" replace />;

  async function submitLocationReview(reportId:number,status:"verified"|"mismatch"|"unable_to_verify") {
    const note=window.prompt(t("Add a short review note (optional):")) ?? "";
    try {
      const response=await fetch(`${API_URL}/api/v1/admin/reports/${reportId}/location-review`,{method:"PATCH",headers:{"Authorization":`Bearer ${tokenStore.get()??""}`,"Content-Type":"application/json"},body:JSON.stringify({status,note})});
      if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(body.detail??`Review failed (${response.status})`)}
      setLocationReviews(items=>items.filter(item=>item.id!==reportId));
    } catch(e){setError(e instanceof Error?e.message:t("Could not save location review"))}
  }
  async function searchUsers(e: React.FormEvent) {
    e.preventDefault(); setFilterBusy(true);
    try { const data = await adminRequest<{ items: AdminUser[] }>(`/users?limit=100&search=${encodeURIComponent(search)}`); setUsers(data.items); }
    catch (e) { setError(e instanceof Error ? e.message : t("User search failed")); }
    finally { setFilterBusy(false); }
  }
  async function searchReports(e: React.FormEvent) {
    e.preventDefault(); setFilterBusy(true);
    try { const data = await adminRequest<{ items: AdminReport[] }>(`/reports?limit=100&search=${encodeURIComponent(reportSearch)}`); setReports(data.items); }
    catch (e) { setError(e instanceof Error ? e.message : t("Report search failed")); }
    finally { setFilterBusy(false); }
  }
  if (busy) return <div className="screen-state">{t("Loading command centre…")}</div>;

  return <div className="admin-page">
    <section className="welcome-row">
      <div><p className="eyebrow">{t("System administration")}</p><h1>{t("Command Centre")}</h1><p className="muted">{t("An operational view of people, reports and activity across GovConnectX.")}</p></div>
      <button className="button button-primary" onClick={() => { setBusy(true); void load(); }}>{t("Refresh data")}</button>
    </section>
    {error && <p className="form-error admin-error" role="alert">{error}</p>}

    {overview && <>
      <div className="admin-section-label">{t("PLATFORM OVERVIEW")}</div>
      <section className="admin-stat-grid">
        <AdminStat label={t("Registered users")} value={overview.users.total} hint={`${overview.users.registered_today} ${t("registered today")}`} />
        <AdminStat label={t("Active accounts")} value={overview.users.active} hint={`${overview.users.inactive} ${t("inactive accounts")}`} />
        <AdminStat label={t("All reports")} value={overview.reports.total} hint={`${overview.reports.open} ${t("still open")}`} />
        <AdminStat label={t("Overdue reports")} value={overview.reports.overdue} hint={t("Past their SLA deadline")} />
      </section>
      <section className="admin-split">
        <article className="panel"><h2>{t("Users by role")}</h2><div className="role-breakdown">{Object.entries(overview.users.by_role).map(([role, count]) => <div className="role-line" key={role}><span>{t(role.replaceAll("_", " "))}</span><strong>{count}</strong></div>)}</div></article>
        <article className="panel"><h2>{t("Reports by status")}</h2><div className="role-breakdown">{Object.entries(overview.reports.by_status).map(([status, count]) => <div className="role-line" key={status}><span>{t(status)}</span><strong>{count}</strong></div>)}</div></article>
      </section>
    </>}

    <GeographicOperationsPanel />

    <section className="panel"><div className="panel-heading"><div><h2>{t("Incident GPS verification")}</h2><p className="muted">{t("Review citizen-shared device coordinates against the incident State/LGA selected in the report. This is a human review queue, not an automatic location verdict.")}</p></div><span className="admin-count">{locationReviews.length} pending</span></div>
      {locationReviews.map(item=><article className="oversight-item" key={item.id}><div className="oversight-item-heading"><div><strong>#{item.id} · {item.title}</strong><small>{item.category} · {item.address||t("No address supplied")}</small></div><span className="oversight-priority priority-medium">{t("Pending review")}</span></div><p>{t("Device GPS:")} {item.gps_latitude.toFixed(6)}, {item.gps_longitude.toFixed(6)}</p><p>{t("Citizen-selected incident area:")} {item.incident_state_code||t("No State")} / {item.incident_lga_code||t("No LGA")}</p><div className="form-actions"><button className="button button-primary button-small" onClick={()=>void submitLocationReview(item.id,"verified")}>{t("Mark consistent")}</button><button className="button button-quiet button-small" onClick={()=>void submitLocationReview(item.id,"mismatch")}>{t("Flag mismatch")}</button><button className="button button-quiet button-small" onClick={()=>void submitLocationReview(item.id,"unable_to_verify")}>{t("Unable to verify")}</button></div></article>)}
      {locationReviews.length===0&&<p className="empty-state">{t("No GPS reports are awaiting review.")}</p>}
    </section>

    <section className="panel">
      <div className="panel-heading"><div><h2>{t("Advanced reporting oversight")}</h2><p className="muted">{t("Explainable patterns that may deserve a closer human review · last 30 days.")}</p></div><span className="admin-count">{oversight?.summary.flagged_citizens ?? 0} {t("flagged for review")}</span></div>
      {oversight && <>
        <div className="oversight-stat-grid">
          <div><strong>{oversight.summary.flagged_citizens}</strong><span>{t("Citizens with signals")}</span></div>
          <div><strong>{oversight.summary.high_priority}</strong><span>{t("Multiple signals")}</span></div>
          <div><strong>{oversight.summary.reports_analyzed}</strong><span>{t("Reports analyzed")}</span></div>
        </div>
        <p className="oversight-thresholds">{t("Review thresholds:")} {oversight.thresholds.min_reports}+ {t(t("reports in"))} {oversight.window_days} {t("days")} · {oversight.thresholds.burst_threshold}+ reports in {oversight.thresholds.burst_window_hours} {t("hours")} · {t("repeated report content.")}</p>
        <div className="oversight-list">
          {oversight.items.map(item => <article className="oversight-item" key={item.user.id}>
            <div className="oversight-item-heading">
              <div><strong>{item.user.full_name}</strong><small>{item.user.email} · {item.reports_in_window} {t("reports in")} {oversight.window_days} {t("days")} · max {item.max_reports_in_24h} in 24h</small></div>
              <span className={`oversight-priority priority-${item.review_priority}`}>{item.review_priority} review priority</span>
            </div>
            <ul className="oversight-signals">{item.signals.map(signal => <li key={signal.code}><strong>{signal.label}:</strong> {signal.detail}</li>)}</ul>
            <details className="oversight-reports"><summary>{t("View related reports")} ({item.reports.length})</summary>
              {item.reports.map(report => <div className="oversight-report" key={report.id}><strong>#{report.id} · {report.title}</strong><span>{report.category} · {t(report.status)} · {dateTime(report.created_at, locale)}</span><small>{report.address || t(t("Location not provided"))}</small></div>)}
            </details>
          </article>)}
          {oversight.items.length === 0 && <p className="empty-state">{t("No reporting patterns crossed the current review thresholds.")}</p>}
        </div>
        <p className="oversight-notice">{oversight.notice}</p>
      </>}
    </section>

    <section className="panel">
      <div className="panel-heading"><div><h2>{t("People on the platform")}</h2><p className="muted">{t("Account directory and each citizen’s report contribution.")}</p></div><span className="admin-count">{users.length} {t("shown")}</span></div>
      <form className="admin-search" onSubmit={searchUsers}><input aria-label="Search users" placeholder={t("Search name or email")} value={search} onChange={e => setSearch(e.target.value)} /><button className="button button-quiet button-small" disabled={filterBusy}>{t("Search users")}</button></form>
      <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>{t("User")}</th><th>{t("Role")}</th><th>{t("Reports")}</th><th>{t("Account")}</th><th>{t("Joined")}</th></tr></thead><tbody>
        {users.map(person => <tr key={person.id}><td><strong>{person.full_name}</strong><small>{person.email}</small></td><td><span className="admin-role">{t(person.role.replaceAll("_", " "))}</span></td><td>{person.reports_submitted}</td><td><span className={person.is_active ? "account-active" : "account-inactive"}>{person.is_active ? t("Active") : t("Inactive")}</span></td><td>{dateTime(person.created_at, locale)}</td></tr>)}
      </tbody></table>{users.length === 0 && <p className="empty-state">{t("No users match this search.")}</p>}</div>
    </section>

    <section className="panel">
      <div className="panel-heading"><div><h2>{t("Citizen reports")}</h2><p className="muted">{t("See who reported what, and the current state of each case.")}</p></div><span className="admin-count">{reports.length} {t("shown")}</span></div>
      <form className="admin-search" onSubmit={searchReports}><input aria-label="Search reports" placeholder={t("Search report, category, location or reporter")} value={reportSearch} onChange={e => setReportSearch(e.target.value)} /><button className="button button-quiet button-small" disabled={filterBusy}>{t("Search reports")}</button></form>
      <div className="admin-report-list">{reports.map(report => <article className="admin-report" key={report.id}>
        <div className="admin-report-top"><div><strong>#{report.id} · {report.title}</strong><p>{report.category} · {report.address || "Location not provided"}</p></div><span className={`status-badge status-${report.status.toLowerCase()}`}>{report.status.replaceAll("_", " ")}</span></div>
        <p className="admin-reporter">{t("Reported by")} <strong>{report.reporter?.full_name ?? t("Unknown user")}</strong>{report.reporter ? ` · ${report.reporter.email}` : ""} · {dateTime(report.created_at, locale)}</p>
        <p className="admin-description">{report.description}</p>
      </article>)}{reports.length === 0 && <p className="empty-state">{t("No reports match this search.")}</p>}</div>
    </section>

    <AuditLogPanel />
    <CommunityModerationPanel />
    <GeographicDirectoryPanel />
    <GeographicBulkImportPanel />

    <section className="panel">
      <div className="panel-heading"><div><h2>{t("Recent platform activity")}</h2><p className="muted">{t("Registrations, report status changes and assignments recorded by the platform.")}</p></div></div>
      <div className="activity-list">{activity.map(event => <article className="activity-row" key={event.id}><span className="activity-dot" /><div><p><strong>{event.actor}</strong> <span className="admin-role">{t(event.actor_role.replaceAll("_", " "))}</span> {event.description}</p><small>{dateTime(event.created_at, locale)}</small></div></article>)}</div>
    </section>
    <p className="admin-privacy">{t("This dashboard shows recorded platform actions and report data. It does not monitor private messages, passwords or activity outside GovConnectX.")}</p>
  </div>;
}
function AdminStat({ label, value, hint }: { label: string; value: number; hint: string }) {
  return <article className="stat-card"><span>{label}</span><strong>{value.toLocaleString("en-NG")}</strong><small>{hint}</small></article>;
}
