import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import DepartmentPerformancePanel from "../components/DepartmentPerformancePanel";
import { api } from "../services/api";
import type { Report } from "../types/api";
import { useAuth } from "../state/AuthContext";
import { useLanguage } from "../state/LanguageContext";

const statuses = ["SUBMITTED", "UNDER_REVIEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "REJECTED"];

export default function AgencyDashboardPage() {
  const { user } = useAuth();
  const { t, locale } = useLanguage();
  const [reports, setReports] = useState<Report[]>([]);
  const [status, setStatus] = useState("ALL");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const dateFormat = useMemo(() => new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeStyle: "short" }), [locale]);

  const load = useCallback(async (quiet = false) => {
    if (quiet) setRefreshing(true);
    else setLoading(true);
    setError("");
    try {
      // The API applies the user's department jurisdiction and, for field
      // officers, limits results to reports assigned to that officer.
      setReports(await api.reports());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t("Could not load operational reports."));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [t]);

  useEffect(() => { void load(); }, [load]);

  if (user?.role === "citizen") return <Navigate to="/dashboard" replace />;
  if (user?.role === "system_admin") return <Navigate to="/admin" replace />;

  const isOfficer = user?.role === "official";
  const active = reports.filter(report => !["RESOLVED", "REJECTED"].includes(report.status)).length;
  const overdue = reports.filter(report => report.sla_due_at && new Date(report.sla_due_at).getTime() < Date.now() && !["RESOLVED", "REJECTED"].includes(report.status)).length;
  const visible = reports.filter(report => {
    const matchesStatus = status === "ALL" || report.status === status;
    const term = search.trim().toLowerCase();
    const matchesSearch = !term || [report.title, report.category, report.address ?? "", String(report.id), report.incident_state_code ?? "", report.incident_lga_code ?? ""].some(value => value.toLowerCase().includes(term));
    return matchesStatus && matchesSearch;
  });

  return <>
    <section className="citizen-dashboard-banner">
      <div>
        <p className="eyebrow">{t("AGENCY OPERATIONS")}</p>
        <h2>{isOfficer ? t("My field assignments") : t("Department report queue")}</h2>
        <p>{t("Review reports within your authorised department and geographic coverage, then coordinate the next action.")}</p>
      </div>
      <span className="dashboard-fist" aria-hidden="true">⌖</span>
    </section>

    <section className="welcome-row">
      <div>
        <p className="eyebrow">{t("Agency operations")}</p>
        <h1>{isOfficer ? t("My assigned reports") : t("Reports for my department")}</h1>
        <p className="muted">{user?.department_id ? t("Your report access is restricted by your department and geographic scope.") : t("Your account is not currently linked to a department. Contact a system administrator.")}</p>
      </div>
      <button className="button button-quiet" onClick={() => void load(true)} disabled={refreshing}>{refreshing ? t("Refreshing…") : t("Refresh queue")}</button>
    </section>

    <section className="stat-grid">
      <Stat label={t("Reports in scope")} value={reports.length} hint={t("Visible to your account")} />
      <Stat label={t("Open reports")} value={active} hint={t("Awaiting action or review")} />
      <Stat label={t("Resolved")} value={reports.filter(report => report.status === "RESOLVED").length} hint={t("Marked as resolved")} />
      <Stat label={t("Overdue")} value={overdue} hint={t("Past the configured SLA")} />
    </section>

    <DepartmentPerformancePanel />

    <section className="panel">
      <div className="panel-heading">
        <div><h2>{t("Operational report queue")}</h2><p className="muted">{t("Open a report to review its history, assign an officer, and record progress.")}</p></div>
        <span className="status-badge">{visible.length} {t("shown")}</span>
      </div>
      <div className="form-grid">
        <label>{t("Search reports")}<input value={search} onChange={event => setSearch(event.target.value)} placeholder={t("Search title, location or report number")} /></label>
        <label>{t("Filter by status")}<select value={status} onChange={event => setStatus(event.target.value)}><option value="ALL">{t("All statuses")}</option>{statuses.map(value => <option key={value} value={value}>{t(value)}</option>)}</select></label>
      </div>
      {error && <p className="form-error" role="alert">{error}</p>}
      {loading ? <div className="empty-state">{t("Loading operational reports…")}</div>
        : visible.length === 0 ? <div className="empty-state"><h3>{t("No reports in this queue")}</h3><p>{reports.length ? t("No reports match the selected search or status filter.") : t("Reports appear here only when they fall within your authorised department scope or are assigned to you.")}</p></div>
        : <div className="report-list">{visible.map(report => <Link className="report-row report-row-link" to={`/reports/${report.id}`} key={report.id}>
          <div className="report-symbol">{report.category.slice(0, 1).toUpperCase()}</div>
          <div className="report-main">
            <div className="report-title-line"><h3>{report.title}</h3><span className={`status-badge status-${report.status.toLowerCase()}`}>{t(report.status)}</span></div>
            <p>{report.category} · {report.address || t("Location coordinates")}</p>
            <small>{t("Report number")} #{report.id} · {report.incident_state_code ?? "—"} / {report.incident_lga_code ?? "—"} · {dateFormat.format(new Date(report.created_at))}</small>
          </div>
          <span className="report-open">{t("Open report")} →</span>
        </Link>)}</div>}
    </section>
  </>;
}

function Stat({ label, value, hint }: { label: string; value: number; hint: string }) {
  return <article className="stat-card"><span>{label}</span><strong>{value}</strong><small>{hint}</small></article>;
}
