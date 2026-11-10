import { useEffect, useState } from "react";
import { api } from "../services/api";

export default function DepartmentPerformancePanel() {
  const [data, setData] = useState<Awaited<ReturnType<typeof api.departmentPerformance>> | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api.departmentPerformance().then(value => { if (active) setData(value); })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : "Could not load department metrics."); });
    return () => { active = false; };
  }, []);
  if (error) return <section className="panel"><p className="form-error" role="alert">{error}</p></section>;
  if (!data) return <section className="panel"><p className="muted">Loading department performance…</p></section>;
  return <section className="panel">
    <div className="panel-heading"><div><p className="eyebrow">OPERATIONS OVERVIEW</p><h2>{data.scope === "individual_assignments" ? "My assigned workload" : "Department performance"}</h2><p className="muted">Operational indicators for reports visible to your account.</p></div></div>
    <section className="stat-grid">
      <article className="stat-card"><span>Total reports</span><strong>{data.total_reports}</strong><small>In your authorized scope</small></article>
      <article className="stat-card"><span>Open reports</span><strong>{data.open_reports}</strong><small>Awaiting action or review</small></article>
      <article className="stat-card"><span>Resolved</span><strong>{data.resolved_reports}</strong><small>Marked resolved</small></article>
      <article className="stat-card"><span>Overdue</span><strong>{data.overdue_reports}</strong><small>Past the configured SLA</small></article>
    </section>
    <p className="muted" style={{ marginTop: "1rem" }}>Resolution rate: {data.resolution_rate_percent}% · Average resolution time: {data.average_resolution_hours === null ? "Not enough data" : `${data.average_resolution_hours} hours`}</p>
    <p className="muted">{data.measurement_note}</p>
  </section>;
}
