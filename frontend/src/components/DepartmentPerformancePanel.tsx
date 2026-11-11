import { useEffect, useState } from "react";
import { api } from "../services/api";
import { useLanguage } from "../state/LanguageContext";

export default function DepartmentPerformancePanel() {
  const { t } = useLanguage();
  const [data, setData] = useState<Awaited<ReturnType<typeof api.departmentPerformance>> | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api.departmentPerformance().then(value => { if (active) setData(value); })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : t("Could not load department metrics.")); });
    return () => { active = false; };
  }, []);
  if (error) return <section className="panel"><p className="form-error" role="alert">{error}</p></section>;
  if (!data) return <section className="panel"><p className="muted">{t("Loading department performance…")}</p></section>;
  return <section className="panel">
    <div className="panel-heading"><div><p className="eyebrow">{t("OPERATIONS OVERVIEW")}</p><h2>{data.scope === "individual_assignments" ? t("My assigned workload") : t("Department performance")}</h2><p className="muted">{t("Operational indicators for reports visible to your account.")}</p></div></div>
    <section className="stat-grid">
      <article className="stat-card"><span>{t("Total reports")}</span><strong>{data.total_reports}</strong><small>{t("In your authorized scope")}</small></article>
      <article className="stat-card"><span>{t("Open reports")}</span><strong>{data.open_reports}</strong><small>{t("Awaiting action or review")}</small></article>
      <article className="stat-card"><span>{t("Resolved")}</span><strong>{data.resolved_reports}</strong><small>{t("Marked resolved")}</small></article>
      <article className="stat-card"><span>{t("Overdue")}</span><strong>{data.overdue_reports}</strong><small>{t("Past the configured SLA")}</small></article>
    </section>
    <p className="muted" style={{ marginTop: "1rem" }}>{t("Resolution rate:")} {data.resolution_rate_percent}% · {t("Average resolution time:")} {data.average_resolution_hours === null ? t("Not enough data") : `${data.average_resolution_hours} hours`}</p>
    <p className="muted">{data.measurement_note}</p>
  </section>;
}
