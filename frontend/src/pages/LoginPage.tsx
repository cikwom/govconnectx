import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import ThemeToggle from "../components/ThemeToggle";
import LanguageSelector from "../components/LanguageSelector";
import { useLanguage } from "../state/LanguageContext";
import { useAuth } from "../state/AuthContext";
import { api } from "../services/api";
import type { GeographicState, LocalGovernmentArea } from "../types/api";

export default function LoginPage() {
  const { user, signIn } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [states, setStates] = useState<GeographicState[]>([]);
  const [lgas, setLgas] = useState<LocalGovernmentArea[]>([]);
  const [selectedStateCode, setSelectedStateCode] = useState("");
  const [selectedLgaCode, setSelectedLgaCode] = useState("");
  const [locationLoading, setLocationLoading] = useState(true);
  const [locationError, setLocationError] = useState("");
  const adminPortal = location.pathname === "/admin/login";
  const notice = (location.state as { notice?: string } | null)?.notice;

  useEffect(() => {
    let active = true;
    api.states()
      .then(items => {
        if (!active) return;
        setStates(items);
        setLocationError(items.length ? "" : t("No states are currently available. Please try again later."));
      })
      .catch(() => {
        if (active) setLocationError(t("We could not load the state directory. Check that the GovConnectX API is running, then refresh."));
      })
      .finally(() => { if (active) setLocationLoading(false); });
    return () => { active = false; };
  }, [t]);

  useEffect(() => {
    let active = true;
    setSelectedLgaCode("");
    if (!selectedStateCode) {
      setLgas([]);
      return () => { active = false; };
    }
    api.lgas(selectedStateCode)
      .then(items => {
        if (active) {
          setLgas(items);
          setLocationError(items.length ? "" : t("No local government areas were returned for this state."));
        }
      })
      .catch(() => {
        if (active) {
          setLgas([]);
          setLocationError(t("We could not load LGAs for this state. Please choose the state again or refresh."));
        }
      });
    return () => { active = false; };
  }, [selectedStateCode, t]);

  const selectedState = states.find(state => state.code === selectedStateCode);

  if (user) return <Navigate to={user.role === "system_admin" ? "/admin" : "/dashboard"} replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const signedInUser = await signIn(email, password, adminPortal ? ["system_admin", "department_admin", "supervisor", "official"] : undefined);

      const destination = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      navigate(destination || (signedInUser.role === "system_admin" ? "/admin" : "/dashboard"), { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : t("Unable to sign in"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-theme-control"><LanguageSelector /><ThemeToggle /></div>
      <section className="auth-aside">
        <Link className="brand brand-inverse" to="/"><span className="brand-mark">G</span><span>GovConnect Nigeria</span></Link>
        <div className="auth-aside-message">
          <p className="eyebrow">{t("CITIZEN VOICE · PUBLIC ACTION")}</p>
          <h1>{t("Good communities grow when every voice counts.")}</h1>
          <p>{t("Speak up about the things that matter. Follow progress. Be part of a more responsive public service.")}</p>
          <div className="auth-aside-points"><span><b>✓</b> {t("Report local issues")}</span><span><b>✓</b> {t("Follow real updates")}</span><span><b>✓</b> {t("Stay part of the change")}</span></div>
        </div>
        <span className="aside-foot">{t("A clearer connection between citizens and public institutions.")}</span>
        <div className="auth-decor auth-decor-one" /><div className="auth-decor auth-decor-two" />
      </section>
      <section className="auth-main">
        <div className="auth-card">
          <Link className="auth-back-link" to="/">← {t("Back to home")}</Link>
          <p className="eyebrow">{adminPortal ? t("GOVERNMENT & ADMINISTRATION") : t("WELCOME BACK")}</p>
          <h2>{adminPortal ? t("Government and administration sign in.") : t("Good to see you again.")}</h2>
          <p className="muted">{adminPortal ? t("Use your authorised institutional account to access government operations.") : t("Sign in to follow your reports and community updates.")}</p>
          {notice && <p className="form-success" role="status">{notice}</p>}
          <form className="form-stack auth-form" onSubmit={submit}>
            <label>{t("Email address")}<input type="email" autoComplete="email" placeholder="you@example.com" required value={email} onChange={event => setEmail(event.target.value)} /></label>
            <label>{t("Password")}<input type="password" autoComplete="current-password" placeholder={t("Enter your password")} required value={password} onChange={event => setPassword(event.target.value)} /></label>

            {!adminPortal && <div className="location-form-group">
              <p className="field-heading">{t("Select your region")}</p>
              <p className="muted">{t("Choose your home state to see its geopolitical zone and local government areas. This is optional and does not limit where you can report an issue.")}</p>
              <label>{t("State or FCT")}
                <select value={selectedStateCode} disabled={locationLoading || states.length === 0} onChange={event => setSelectedStateCode(event.target.value)}>
                  <option value="">{locationLoading ? t("Loading states…") : t("Select your state")}</option>
                  {states.map(state => <option key={state.code} value={state.code}>{state.name}</option>)}
                </select>
              </label>
              {selectedState && <p className="form-success" role="status">{t("Geopolitical zone")}: <strong>{selectedState.geopolitical_zone}</strong></p>}
              <label>{t("Local Government Area")}
                <select value={selectedLgaCode} disabled={!selectedStateCode || lgas.length === 0} onChange={event => setSelectedLgaCode(event.target.value)}>
                  <option value="">{selectedStateCode ? (lgas.length ? t("Select your LGA") : t("Loading LGAs…")) : t("Select a state first")}</option>
                  {lgas.map(lga => <option key={lga.code} value={lga.code}>{lga.name}</option>)}
                </select>
              </label>
              {locationError && <p className="form-error" role="alert">{locationError}</p>}
            </div>}

            {error && <p className="form-error" role="alert">{error}</p>}
            <button className="button button-primary button-full auth-submit" disabled={busy}>{busy ? t("Signing you in…") : t("Sign in to GovConnect")} <span aria-hidden="true">→</span></button>
          </form>
          <p className="auth-switch"><Link to="/forgot-password">{t("Forgot your password?")}</Link></p>
          {adminPortal
            ? <p className="auth-switch">{t("Citizen account?")} <Link to="/login">{t("Citizen sign in")}</Link></p>
            : <p className="auth-switch">{t("Government staff?")} <Link to="/admin/login">{t("Use the government sign-in")}</Link></p>}
          {!adminPortal && <p className="auth-switch">{t("New to GovConnect?")} <Link to="/register">{t("Create an account")}</Link></p>}
          <p className="auth-secure-note"><span>●</span> {t("Your account and reports stay protected.")}</p>
        </div>
      </section>
    </main>
  );
}
