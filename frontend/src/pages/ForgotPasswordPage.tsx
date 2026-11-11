import { useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const result = await api.requestPasswordReset(email);
      setMessage(result.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "We could not process your request. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-main">
        <div className="auth-card">
          <Link className="auth-back-link" to="/login">← Back to sign in</Link>
          <p className="eyebrow">ACCOUNT RECOVERY</p>
          <h2>Forgot your password?</h2>
          <p className="muted">Enter the email address registered to your GovConnect account. If it matches an active account, we will send a secure recovery link.</p>
          <form className="form-stack auth-form" onSubmit={submit}>
            <label>Email address<input type="email" autoComplete="email" required value={email} onChange={event => setEmail(event.target.value)} /></label>
            {error && <p className="form-error" role="alert">{error}</p>}
            {message && <p className="form-success" role="status">{message}</p>}
            <button className="button button-primary button-full" disabled={busy}>{busy ? "Sending…" : "Send recovery link"}</button>
          </form>
          <p className="auth-switch">Government or administrator account? <Link to="/admin/login">Return to government sign in</Link></p>
        </div>
      </section>
    </main>
  );
}
