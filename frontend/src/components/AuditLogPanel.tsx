import { useEffect, useState } from "react";
import { tokenStore } from "../services/api";

type AuditItem = {
  id: number;
  actor: { id: number; name: string; role: string } | null;
  action: string;
  entity_type: string;
  entity_id: number | null;
  summary: string;
  details: Record<string, unknown>;
  created_at: string | null;
};

const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
const dateTime = (value: string | null) => value ? new Intl.DateTimeFormat("en-NG", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "—";

export default function AuditLogPanel() {
  const [items, setItems] = useState<AuditItem[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    fetch(`${API_URL}/api/v1/admin/audit-logs?limit=50`, {
      headers: { Authorization: `Bearer ${tokenStore.get() ?? ""}` },
    })
      .then(async response => {
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(body.detail ?? `Audit log request failed (${response.status})`);
        }
        return response.json() as Promise<{ items: AuditItem[] }>;
      })
      .then(data => { if (active) setItems(data.items); })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : "Could not load audit events."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  return (
    <section className="panel">
      <div className="panel-heading"><div><h2>Accountability audit trail</h2><p className="muted">Recorded report submissions, assignments, workflow changes, comments and GPS reviews.</p></div><span className="admin-count">{items.length} recent events</span></div>
      {loading && <p className="muted">Loading audit events…</p>}
      {error && <p className="form-error" role="alert">{error}</p>}
      {!loading && !error && items.length === 0 && <p className="empty-state">No audit events have been recorded yet.</p>}
      <div className="activity-list">
        {items.map(item => <article className="activity-row" key={item.id}>
          <span className="activity-dot" />
          <div><p><strong>{item.actor?.name ?? "System"}</strong> <span className="admin-role">{item.actor?.role?.replaceAll("_", " ") ?? "system"}</span> {item.summary}</p>
            <small>{item.action} · {item.entity_type}{item.entity_id ? ` #${item.entity_id}` : ""} · {dateTime(item.created_at)}</small>
          </div>
        </article>)}
      </div>
    </section>
  );
}
