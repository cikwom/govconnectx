import { useCallback, useEffect, useState } from "react";
import { api } from "../services/api";
import { useLanguage } from "../state/LanguageContext";

type Invitation = {
  id: number; email: string; full_name: string; role: string; department_id: number | null;
  expires_at: string; accepted_at: string | null; revoked_at: string | null; status: string;
  created_at: string | null;
};
type Department = { id: number; name: string };

export default function StaffInvitationPanel() {
  const { t } = useLanguage();
  const [items, setItems] = useState<Invitation[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("official");
  const [departmentId, setDepartmentId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [devUrl, setDevUrl] = useState("");

  const load = useCallback(async () => {
    try {
      const [invitations, departmentList] = await Promise.all([
        fetch("/api/v1/admin/staff-invitations", { headers: { Authorization: `Bearer ${localStorage.getItem("govconnect_token") ?? ""}` } }),
        api.departments(),
      ]);
      if (!invitations.ok) throw new Error(t("Could not load staff invitations."));
      const data = await invitations.json();
      setItems(data.items ?? []);
      setDepartments(departmentList);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t("Could not load staff invitations."));
    }
  }, [t]);

  useEffect(() => { void load(); }, [load]);

  async function createInvitation(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true); setError(""); setNotice(""); setDevUrl("");
    try {
      const response = await fetch("/api/v1/admin/staff-invitations", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("govconnect_token") ?? ""}` },
        body: JSON.stringify({ email, full_name: fullName, role, department_id: departmentId ? Number(departmentId) : null }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail ?? t("Could not create invitation."));
      setNotice(t("Invitation created. Email delivery will be attempted in the background."));
      setDevUrl(body.development_invitation_url ?? "");
      setEmail(""); setFullName(""); setRole("official"); setDepartmentId("");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t("Could not create invitation."));
    } finally { setBusy(false); }
  }

  async function revoke(id: number) {
    if (!window.confirm(t("Revoke this staff invitation?"))) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const response = await fetch(`/api/v1/admin/staff-invitations/${id}/revoke`, {
        method: "POST", headers: { Authorization: `Bearer ${localStorage.getItem("govconnect_token") ?? ""}` },
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail ?? t("Could not revoke invitation."));
      setNotice(t("Invitation revoked."));
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t("Could not revoke invitation."));
    } finally { setBusy(false); }
  }

  return <section className="panel">
    <div className="panel-heading"><div><h2>{t("Staff invitations")}</h2><p className="muted">{t("Invite agency officials and supervisors with time-limited, single-use onboarding links.")}</p></div><span className="admin-count">{items.filter(item => item.status === "pending").length} {t("pending")}</span></div>
    {error && <p className="form-error" role="alert">{error}</p>}
    {notice && <p className="form-success" role="status">{notice}</p>}
    {devUrl && <div className="form-success"><p>{t("Development invitation link (copy and share securely):")}</p><input readOnly value={devUrl} aria-label={t("Development invitation link")} /><button type="button" className="button button-quiet button-small" onClick={() => void navigator.clipboard?.writeText(devUrl)}>{t("Copy invitation link")}</button></div>}
    <form className="admin-search" onSubmit={createInvitation}>
      <input aria-label={t("Staff full name")} placeholder={t("Staff full name")} value={fullName} onChange={event => setFullName(event.target.value)} required minLength={2} maxLength={150}/>
      <input aria-label={t("Staff email")} type="email" placeholder={t("Staff email")} value={email} onChange={event => setEmail(event.target.value)} required maxLength={255}/>
      <select aria-label={t("Staff role")} value={role} onChange={event => setRole(event.target.value)}>
        <option value="official">{t("Official / Field officer")}</option><option value="supervisor">{t("Supervisor")}</option><option value="department_admin">{t("Department administrator")}</option>
      </select>
      <select aria-label={t("Department")} value={departmentId} onChange={event => setDepartmentId(event.target.value)}>
        <option value="">{t("No department yet")}</option>{departments.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
      </select>
      <button className="button button-primary" disabled={busy || !email.trim() || fullName.trim().length < 2}>{busy ? t("Working…") : t("Create staff invitation")}</button>
    </form>
    <div className="admin-report-list">{items.map(item => <article className="admin-report" key={item.id}>
      <div className="admin-report-top"><div><strong>{item.full_name}</strong><p>{item.email} · {t(item.role.replaceAll("_", " "))}</p></div><span className={item.status === "pending" ? "account-active" : "account-inactive"}>{t(item.status)}</span></div>
      <p className="muted">{t("Expires:")} {new Date(item.expires_at).toLocaleString()}</p>
      {item.status === "pending" && <button className="button button-quiet button-small" disabled={busy} onClick={() => void revoke(item.id)}>{t("Revoke invitation")}</button>}
    </article>)}</div>
    {items.length === 0 && <p className="empty-state">{t("No staff invitations yet.")}</p>}
  </section>;
}
