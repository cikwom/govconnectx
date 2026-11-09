import { useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import ThemeToggle from "../components/ThemeToggle";
import { useAuth } from "../state/AuthContext";

export default function LoginPage() {
  const { user, signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  if (user) return <Navigate to={user.role === "system_admin" ? "/admin" : "/dashboard"} replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const signedInUser = await signIn(email, password);
      const destination = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      navigate(destination || (signedInUser.role === "system_admin" ? "/admin" : "/dashboard"), { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-theme-control"><ThemeToggle /></div>
      <section className="auth-aside">
        <Link className="brand brand-inverse" to="/"><span className="brand-mark">G</span><span>GovConnect Nigeria</span></Link>
        <div className="auth-aside-message">
          <p className="eyebrow">CITIZEN VOICE · PUBLIC ACTION</p>
          <h1>Good communities grow when every voice counts.</h1>
          <p>Speak up about the things that matter. Follow progress. Be part of a more responsive public service.</p>
          <div className="auth-aside-points"><span><b>✓</b> Report local issues</span><span><b>✓</b> Follow real updates</span><span><b>✓</b> Stay part of the change</span></div>
        </div>
        <span className="aside-foot">A clearer connection between citizens and public institutions.</span>
        <div className="auth-decor auth-decor-one" /><div className="auth-decor auth-decor-two" />
      </section>
      <section className="auth-main">
        <div className="auth-card">
          <Link className="auth-back-link" to="/">← Back to home</Link>
          <p className="eyebrow">WELCOME BACK</p>
          <h2>Good to see you again.</h2>
          <p className="muted">Sign in to follow your reports and community updates.</p>
          <form className="form-stack auth-form" onSubmit={submit}>
            <label>Email address<input type="email" autoComplete="email" placeholder="you@example.com" required value={email} onChange={event => setEmail(event.target.value)} /></label>
            <label>Password<input type="password" autoComplete="current-password" placeholder="Enter your password" required value={password} onChange={event => setPassword(event.target.value)} /></label>
            {error && <p className="form-error" role="alert">{error}</p>}
            <button className="button button-primary button-full auth-submit" disabled={busy}>{busy ? "Signing you in…" : "Sign in to GovConnect"} <span aria-hidden="true">→</span></button>
          </form>
          <p className="auth-switch">New to GovConnect? <Link to="/register">Create an account</Link></p>
          <p className="auth-secure-note"><span>●</span> Your account and reports stay protected.</p>
        </div>
      </section>
    </main>
  );
}
