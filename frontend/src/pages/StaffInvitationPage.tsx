import { FormEvent, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../services/api";

export default function StaffInvitationPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token") ?? "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(""); setSuccess("");
    if (password.length < 12) { setError("Use at least 12 characters for your password."); return; }
    if (password !== confirm) { setError("The passwords do not match."); return; }
    setBusy(true);
    try {
      const result = await api.acceptStaffInvitation(token, password);
      setSuccess(result.message);
      window.setTimeout(() => navigate("/login", { replace: true }), 1200);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "This invitation could not be accepted."); }
    finally { setBusy(false); }
  }

  return <main className="auth-page"><section className="auth-card">
    <p className="eyebrow">GovConnectX staff onboarding</p><h1>Activate your staff account</h1>
    <p className="muted">Create a password to activate the staff account associated with this invitation. Links can only be used once and expire after 72 hours.</p>
    {!token && <p className="form-error" role="alert">This invitation link is missing its token. Ask your administrator for a new invitation.</p>}
    {error && <p className="form-error" role="alert">{error}</p>}
    {success && <p className="form-success" role="status">{success}</p>}
    {token && <form onSubmit={submit} className="auth-form">
      <label htmlFor="staff-invite-password">New password</label><input id="staff-invite-password" type="password" autoComplete="new-password" minLength={12} maxLength={128} value={password} onChange={event => setPassword(event.target.value)} required />
      <label htmlFor="staff-invite-confirm">Confirm password</label><input id="staff-invite-confirm" type="password" autoComplete="new-password" minLength={12} maxLength={128} value={confirm} onChange={event => setConfirm(event.target.value)} required />
      <button className="button button-primary" disabled={busy || Boolean(success)}>{busy ? "Activating…" : "Activate staff account"}</button>
    </form>}
    <p className="muted"><Link to="/login">Return to sign in</Link></p>
  </section></main>;
}
