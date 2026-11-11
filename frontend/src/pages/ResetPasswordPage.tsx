import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../services/api";

export default function ResetPasswordPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token") ?? "";
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (password !== confirmPassword) {
      setError("The passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      await api.completePasswordReset(token, password);
      navigate("/login", { replace: true, state: { notice: "Your password has been reset. Please sign in with your new password." } });
    } catch (err) {
      setError(err instanceof Error ? err.message : "We could not reset your password. Request a new link.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-main">
        <div className="auth-card">
          <Link className="auth-back-link" to="/login">← Back to sign in</Link>
          <p className="eyebrow">SECURE ACCOUNT RECOVERY</p>
          <h2>Choose a new password</h2>
          {!token ? <p className="form-error" role="alert">This recovery link is missing its token. Request a new link.</p> : <p className="muted">Use at least 8 characters. Your existing signed-in sessions will be revoked after the password changes.</p>}
          <form className="form-stack auth-form" onSubmit={submit}>
            <label>New password<input type="password" autoComplete="new-password" minLength={8} maxLength={128} required value={password} onChange={event => setPassword(event.target.value)} /></label>
            <label>Confirm new password<input type="password" autoComplete="new-password" minLength={8} maxLength={128} required value={confirmPassword} onChange={event => setConfirmPassword(event.target.value)} /></label>
            {error && <p className="form-error" role="alert">{error}</p>}
            <button className="button button-primary button-full" disabled={busy || !token}>{busy ? "Updating password…" : "Reset password"}</button>
          </form>
          <p className="auth-switch"><Link to="/forgot-password">Request another recovery link</Link></p>
        </div>
      </section>
    </main>
  );
}
