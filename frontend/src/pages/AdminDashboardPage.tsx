import { useCallback, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { tokenStore } from "../services/api";
import { useAuth } from "../state/AuthContext";
import GeographicOperationsPanel from "../components/GeographicOperationsPanel";

type Overview = {
  users: { total: number; active: number; inactive: number; by_role: Record<string, number>; registered_today: number };
  reports: { total: number; by_status: Record<string, number>; open: number; overdue: number };
};
type AdminUser = { id: number; full_name: string; email: string; role: string; is_active: boolean; created_at: string | null; reports_submitted: number };
type Activity = { id: string; type: string; actor: string; actor_role: string; description: string; report_id: number | null; created_at: string | null };
type AdminReport = { id: number; title: string; description: string; category: string; status: string; address: string | null; created_at: string | null; reporter: { id: number; full_name: string; email: string } | null };
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
const dateTime = (value: string | null) => value ? new Intl.DateTimeFormat("en-NG", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "—";

export default function AdminDashboardPage() {
  const { user } = useAuth();
  const [overview, setOverview] = useState<Overview | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [reports, setReports] = useState<AdminReport[]>([]);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [oversight, setOversight] = useState<Oversight | null>(null);
  const [search, setSearch] = useState("");
  const [reportSearch, setReportSearch] = useState("");
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [filterBusy, setFilterBusy] = useState(false);

  const load = useCallback(async () => {
    setError("");
    try {
      const [summary, people, reportList, events, patterns] = await Promise.all([
        adminRequest<Overview>("/overview"),
        adminRequest<{ items: AdminUser[] }>("/users?limit=100"),
        adminRequest<{ items: AdminReport[] }>("/reports?limit=100"),
        adminRequest<Activity[]>("/activity?limit=35"),
        adminRequest<Oversight>("/oversight?window_days=30"),
      ]);
      setOverview(summary);
      setUsers(people.items);
      setReports(reportList.items);
      setActivity(events);
      setOversight(patterns);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load admin data");
    } finally {
      setBusy(false);
      setFilterBusy(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);
  if (user && user.role !== "system_admin") return <Navigate to="/dashboard" replace />;

  async function searchUsers(e: React.FormEvent) {
    e.preventDefault(); setFilterBusy(true);
    try { const data = await adminRequest<{ items: AdminUser[] }>(`/users?limit=100&search=${encodeURIComponent(search)}`); setUsers(data.items); }
    catch (e) { setError(e instanceof Error ? e.message : "User search failed"); }
    finally { setFilterBusy(false); }
  }
  async function searchReports(e: React.FormEvent) {
    e.preventDefault(); setFilterBusy(true);
    try { const data = await adminRequest<{ items: AdminReport[] }>(`/reports?limit=100&search=${encodeURIComponent(reportSearch)}`); setReports(data.items); }
    catch (e) { setError(e instanceof Error ? e.message : "Report search failed"); }
    finally { setFilterBusy(false); }
  }
  if (busy) return <div className="screen-state">Loading command centre…</div>;

  return <div className="admin-page">
    <section className="welcome-row">
      <div><p className="eyebrow">SYSTEM ADMINISTRATION</p><h1>Command Centre</h1><p className="muted">An operational view of people, reports and activity across GovConnectX.</p></div>
      <button className="button button-primary" onClick={() => { setBusy(true); void load(); }}>Refresh data</button>
    </section>
    {error && <p className="form-error admin-error" role="alert">{error}</p>}

    {overview && <>
      <div className="admin-section-label">PLATFORM OVERVIEW</div>
      <section className="admin-stat-grid">
        <AdminStat label="Registered users" value={overview.users.total} hint={`${overview.users.registered_today} registered today`} />
        <AdminStat label="Active accounts" value={overview.users.active} hint={`${overview.users.inactive} inactive accounts`} />
        <AdminStat label="All reports" value={overview.reports.total} hint={`${overview.reports.open} still open`} />
        <AdminStat label="Overdue reports" value={overview.reports.overdue} hint="Past their SLA deadline" />
      </section>
      <section className="admin-split">
        <article className="panel"><h2>Users by role</h2><div className="role-breakdown">{Object.entries(overview.users.by_role).map(([role, count]) => <div className="role-line" key={role}><span>{role.replaceAll("_", " ")}</span><strong>{count}</strong></div>)}</div></article>
        <article className="panel"><h2>Reports by status</h2><div className="role-breakdown">{Object.entries(overview.reports.by_status).map(([status, count]) => <div className="role-line" key={status}><span>{status.replaceAll("_", " ")}</span><strong>{count}</strong></div>)}</div></article>
      </section>
    </>}

    <GeographicOperationsPanel />

    <section className="panel">
      <div className="panel-heading"><div><h2>Advanced reporting oversight</h2><p className="muted">Explainable patterns that may deserve a closer human review · last 30 days.</p></div><span className="admin-count">{oversight?.summary.flagged_citizens ?? 0} flagged for review</span></div>
      {oversight && <>
        <div className="oversight-stat-grid">
          <div><strong>{oversight.summary.flagged_citizens}</strong><span>Citizens with signals</span></div>
          <div><strong>{oversight.summary.high_priority}</strong><span>Multiple signals</span></div>
          <div><strong>{oversight.summary.reports_analyzed}</strong><span>Reports analyzed</span></div>
        </div>
        <p className="oversight-thresholds">Review thresholds: {oversight.thresholds.min_reports}+ reports in {oversight.window_days} days · {oversight.thresholds.burst_threshold}+ reports in {oversight.thresholds.burst_window_hours} hours · repeated report content.</p>
        <div className="oversight-list">
          {oversight.items.map(item => <article className="oversight-item" key={item.user.id}>
            <div className="oversight-item-heading">
              <div><strong>{item.user.full_name}</strong><small>{item.user.email} · {item.reports_in_window} reports in {oversight.window_days} days · max {item.max_reports_in_24h} in 24h</small></div>
              <span className={`oversight-priority priority-${item.review_priority}`}>{item.review_priority} review priority</span>
            </div>
            <ul className="oversight-signals">{item.signals.map(signal => <li key={signal.code}><strong>{signal.label}:</strong> {signal.detail}</li>)}</ul>
            <details className="oversight-reports"><summary>View related reports ({item.reports.length})</summary>
              {item.reports.map(report => <div className="oversight-report" key={report.id}><strong>#{report.id} · {report.title}</strong><span>{report.category} · {report.status.replaceAll("_", " ")} · {dateTime(report.created_at)}</span><small>{report.address || "Location not provided"}</small></div>)}
            </details>
          </article>)}
          {oversight.items.length === 0 && <p className="empty-state">No reporting patterns crossed the current review thresholds.</p>}
        </div>
        <p className="oversight-notice">{oversight.notice}</p>
      </>}
    </section>

    <section className="panel">
      <div className="panel-heading"><div><h2>People on the platform</h2><p className="muted">Account directory and each citizen’s report contribution.</p></div><span className="admin-count">{users.length} shown</span></div>
      <form className="admin-search" onSubmit={searchUsers}><input aria-label="Search users" placeholder="Search name or email" value={search} onChange={e => setSearch(e.target.value)} /><button className="button button-quiet button-small" disabled={filterBusy}>Search users</button></form>
      <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>User</th><th>Role</th><th>Reports</th><th>Account</th><th>Joined</th></tr></thead><tbody>
        {users.map(person => <tr key={person.id}><td><strong>{person.full_name}</strong><small>{person.email}</small></td><td><span className="admin-role">{person.role.replaceAll("_", " ")}</span></td><td>{person.reports_submitted}</td><td><span className={person.is_active ? "account-active" : "account-inactive"}>{person.is_active ? "Active" : "Inactive"}</span></td><td>{dateTime(person.created_at)}</td></tr>)}
      </tbody></table>{users.length === 0 && <p className="empty-state">No users match this search.</p>}</div>
    </section>

    <section className="panel">
      <div className="panel-heading"><div><h2>Citizen reports</h2><p className="muted">See who reported what, and the current state of each case.</p></div><span className="admin-count">{reports.length} shown</span></div>
      <form className="admin-search" onSubmit={searchReports}><input aria-label="Search reports" placeholder="Search report, category, location or reporter" value={reportSearch} onChange={e => setReportSearch(e.target.value)} /><button className="button button-quiet button-small" disabled={filterBusy}>Search reports</button></form>
      <div className="admin-report-list">{reports.map(report => <article className="admin-report" key={report.id}>
        <div className="admin-report-top"><div><strong>#{report.id} · {report.title}</strong><p>{report.category} · {report.address || "Location not provided"}</p></div><span className={`status-badge status-${report.status.toLowerCase()}`}>{report.status.replaceAll("_", " ")}</span></div>
        <p className="admin-reporter">Reported by <strong>{report.reporter?.full_name ?? "Unknown user"}</strong>{report.reporter ? ` · ${report.reporter.email}` : ""} · {dateTime(report.created_at)}</p>
        <p className="admin-description">{report.description}</p>
      </article>)}{reports.length === 0 && <p className="empty-state">No reports match this search.</p>}</div>
    </section>

    <section className="panel">
      <div className="panel-heading"><div><h2>Recent platform activity</h2><p className="muted">Registrations, report status changes and assignments recorded by the platform.</p></div></div>
      <div className="activity-list">{activity.map(event => <article className="activity-row" key={event.id}><span className="activity-dot" /><div><p><strong>{event.actor}</strong> <span className="admin-role">{event.actor_role.replaceAll("_", " ")}</span> {event.description}</p><small>{dateTime(event.created_at)}</small></div></article>)}</div>
    </section>
    <p className="admin-privacy">This dashboard shows recorded platform actions and report data. It does not monitor private messages, passwords or activity outside GovConnectX.</p>
  </div>;
}
function AdminStat({ label, value, hint }: { label: string; value: number; hint: string }) {
  return <article className="stat-card"><span>{label}</span><strong>{value.toLocaleString("en-NG")}</strong><small>{hint}</small></article>;
}
