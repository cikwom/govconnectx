import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import ThemeToggle from "../components/ThemeToggle";
import LanguageSelector from "../components/LanguageSelector";
import { useLanguage } from "../state/LanguageContext";
import { api } from "../services/api";
import type { GeographicState, LocalGovernmentArea } from "../types/api";
import { useAuth } from "../state/AuthContext";

export default function RegisterPage() {
  const { user, signUp } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [states, setStates] = useState<GeographicState[]>([]);
  const [lgas, setLgas] = useState<LocalGovernmentArea[]>([]);
  const [homeStateCode, setHomeStateCode] = useState("");
  const [homeLgaCode, setHomeLgaCode] = useState("");
  const [locationError, setLocationError] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.states().then(setStates).catch(() => setLocationError(t("We could not load the state directory. Please refresh and try again.")));
  }, []);

  useEffect(() => {
    setHomeLgaCode("");
    if (!homeStateCode) { setLgas([]); return; }
    api.lgas(homeStateCode).then(setLgas).catch(() => setLocationError(t("We could not load the local government areas for that state.")));
  }, [homeStateCode]);

  if (user) return <Navigate to="/dashboard" replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await signUp({ full_name: fullName, email, password, home_state_code: homeStateCode, home_lga_code: homeLgaCode });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : t("Unable to create your account"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-theme-control"><LanguageSelector /><ThemeToggle /></div>
      <section className="auth-aside">
        <Link className="brand brand-inverse" to="/"><span className="brand-mark">G</span><span>GovConnect Nigeria</span></Link>
        <div>
          <p className="eyebrow">{t("CITIZEN VOICE · PUBLIC ACTION")}</p>
          <h1>{t("Your community. Your voice. Real accountability.")}</h1>
          <p>{t("Create an account to submit reports and follow their progress.")}</p>
        </div>
        <span className="aside-foot">{t("Public registration creates a citizen account.")}</span>
      </section>
      <section className="auth-main">
        <div className="auth-card">
          <Link className="auth-back-link" to="/">← {t("Back to home")}</Link>
          <p className="eyebrow">{t("GET STARTED")}</p>
          <h2>{t("Create your account")}</h2>
          <p className="muted">{t("Choose your home area so we can show you relevant local information.")}</p>
          <form className="form-stack" onSubmit={submit}>
            <label>{t("Full name")}<input autoComplete="name" minLength={2} required value={fullName} onChange={event => setFullName(event.target.value)} /></label>
            <label>{t("Email address")}<input type="email" autoComplete="email" required value={email} onChange={event => setEmail(event.target.value)} /></label>
            <label>{t("Password")}<input type="password" autoComplete="new-password" minLength={8} maxLength={128} required value={password} onChange={event => setPassword(event.target.value)} /><small>{t("Use at least 8 characters.")}</small></label>
            <div className="location-form-group">
              <p className="field-heading">{t("Your home area")}</p>
              <p className="muted">{t("This is used for local updates. It does not restrict where you can report an incident.")}</p>
              <label>{t("State or FCT")}
                <select required value={homeStateCode} onChange={event => setHomeStateCode(event.target.value)}>
                  <option value="">{t("Select your state")}</option>
                  {states.map(state => <option key={state.code} value={state.code}>{state.name} · {state.geopolitical_zone}</option>)}
                </select>
              </label>
              <label>{t("Local Government Area")}
                <select required disabled={!homeStateCode || lgas.length === 0} value={homeLgaCode} onChange={event => setHomeLgaCode(event.target.value)}>
                  <option value="">{t("Select your LGA")}</option>
                  {lgas.map(lga => <option key={lga.code} value={lga.code}>{lga.name}</option>)}
                </select>
              </label>
              {locationError && <p className="form-error" role="alert">{locationError}</p>}
            </div>
            <label className="legal-consent">
              <input type="checkbox" required checked={acceptedTerms} onChange={event => setAcceptedTerms(event.target.checked)} />
              <span>{t("I agree to the")} <Link to="/terms" target="_blank" rel="noreferrer">Terms of Use</Link> {t("and confirm that I have read the")} <Link to="/privacy" target="_blank" rel="noreferrer">Privacy Notice</Link>.</span>
            </label>
            {error && <p className="form-error" role="alert">{error}</p>}
            <button className="button button-primary button-full" disabled={busy || !acceptedTerms || !homeStateCode || !homeLgaCode || !!locationError}>{busy ? t("Creating account…") : t("Create account")}</button>
          </form>
          <p className="auth-switch">{t("Already registered?")} <Link to="/login">{t("Sign in")}</Link></p>
          <p className="auth-legal-links"><Link to="/terms">Terms of Use</Link><span>·</span><Link to="/privacy">Privacy Notice</Link></p>
        </div>
      </section>
    </main>
  );
}
