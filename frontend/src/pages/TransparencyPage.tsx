import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import ThemeToggle from "../components/ThemeToggle";
import LanguageSelector from "../components/LanguageSelector";
import { useLanguage } from "../state/LanguageContext";

type Transparency = {
  updated_at: string;
  reports: { total: number; open: number; resolved: number; rejected: number; resolution_rate_percent: number };
  departments: { active: number };
  by_state: { state_code: string; state_name: string; reports: number | null; suppressed: boolean }[];
  by_category: { category: string; reports: number }[];
  privacy_note: string;
};

const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export default function TransparencyPage() {
  const { t, locale } = useLanguage();
  const [data, setData] = useState<Transparency | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    fetch(`${API_URL}/api/v1/public/transparency`)
      .then(async response => {
        if (!response.ok) throw new Error("Transparency statistics are temporarily unavailable.");
        return response.json() as Promise<Transparency>;
      })
      .then(value => { if (active) setData(value); })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : "Could not load public statistics."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  return (
    <main className="home-page">
      <header className="home-nav">
        <Link className="brand" to="/"><span className="brand-mark">G</span><span>GovConnect<span className="brand-light"> Nigeria</span></span></Link>
        <nav className="home-nav-actions" aria-label="Main navigation">
          <Link to="/">{t("Home")}</Link>
          <LanguageSelector />
          <ThemeToggle />
          <Link className="button button-primary" to="/register">{t("Get started")}</Link>
        </nav>
      </header>
      <section className="page-content" style={{ minHeight: "70vh" }}>
        <div className="welcome-row">
          <div><p className="eyebrow">OPEN GOVERNANCE · PUBLIC INFORMATION</p><h1>Transparency dashboard</h1><p className="muted">A public view of aggregate reports and service-response activity across GovConnect Nigeria.</p></div>
        </div>
        {loading && <div className="panel empty-state">Loading public statistics…</div>}
        {error && <div className="panel"><p className="form-error" role="alert">{error}</p><p className="muted">Please try again later.</p></div>}
        {data && <>
          <section className="admin-stat-grid">
            <article className="stat-card"><span>Reports received</span><strong>{data.reports.total.toLocaleString("en-NG")}</strong><small>All reports recorded on the platform</small></article>
            <article className="stat-card"><span>Open reports</span><strong>{data.reports.open.toLocaleString("en-NG")}</strong><small>Awaiting action or review</small></article>
            <article className="stat-card"><span>Resolved reports</span><strong>{data.reports.resolved.toLocaleString("en-NG")}</strong><small>Marked resolved in the workflow</small></article>
            <article className="stat-card"><span>Resolution rate</span><strong>{data.reports.resolution_rate_percent}%</strong><small>Resolved as a share of all reports</small></article>
          </section>
          <section className="panel">
            <div className="panel-heading"><div><h2>Reports by state</h2><p className="muted">Small counts are suppressed to protect community privacy.</p></div></div>
            <div className="role-breakdown">
              {data.by_state.map(item => <div className="role-line" key={item.state_code}><span>{item.state_name}</span><strong>{item.suppressed ? "Fewer than 5" : (item.reports ?? 0).toLocaleString("en-NG")}</strong></div>)}
            </div>
          </section>
          <section className="panel">
            <div className="panel-heading"><div><h2>Report categories</h2><p className="muted">Only categories with at least five reports are displayed.</p></div></div>
            {data.by_category.length ? <div className="role-breakdown">{data.by_category.map(item => <div className="role-line" key={item.category}><span>{item.category}</span><strong>{item.reports.toLocaleString("en-NG")}</strong></div>)}</div> : <p className="muted">There are not yet enough reports to publish category totals.</p>}
          </section>
          <p className="muted" style={{ fontSize: ".8rem" }}>{data.privacy_note} Active departments: {data.departments.active}. Updated {new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeStyle: "short" }).format(new Date(data.updated_at))}.</p>
        </>}
      </section>
      <footer className="home-footer"><Link className="brand" to="/"><span className="brand-mark">G</span><span>GovConnect<span className="brand-light"> Nigeria</span></span></Link><span>Public aggregate information only.</span><nav className="home-legal-links"><Link to="/terms">Terms of Use</Link><Link to="/privacy">Privacy Notice</Link></nav></footer>
    </main>
  );
}
