import { useEffect, useState } from "react";
import { api } from "../services/api";
import { useLanguage, type Language } from "../state/LanguageContext";

export default function PreferencesPage() {
  const { language, setLanguage, t } = useLanguage();
  const [email, setEmail] = useState(true);
  const [inApp, setInApp] = useState(true);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let active = true;
    api.preferences().then(value => {
      if (!active) return;
      setEmail(value.email_notifications);
      setInApp(value.in_app_notifications);
      // Preserve an unsaved language choice made in the current browser.
      if (!localStorage.getItem("govconnectx_language")) setLanguage(value.preferred_language);
    }).catch(reason => {
      if (active) setError(reason instanceof Error ? reason.message : "Could not load preferences.");
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [setLanguage]);

  async function save() {
    setBusy(true); setError(""); setNotice("");
    try {
      const saved = await api.updatePreferences({ email_notifications: email, in_app_notifications: inApp, preferred_language: language });
      setLanguage(saved.preferred_language);
      setNotice(t("Your preferences have been saved."));
    } catch (reason) { setError(reason instanceof Error ? reason.message : t("Could not save preferences.")); }
    finally { setBusy(false); }
  }

  return <section className="panel">
    <p className="eyebrow">{t("ACCOUNT SETTINGS")}</p>
    <h1>{t("Preferences")}</h1>
    <p className="muted">{t("Choose your interface language and notification preferences.")}</p>
    {loading ? <p className="empty-state">{t("Loading preferences…")}</p> : <>
      <div className="form-grid" style={{ marginTop: "1.5rem" }}>
        <label className="field-wide">{t("Preferred language")}
          <select value={language} onChange={event => setLanguage(event.target.value as Language)}>
            <option value="en">English</option><option value="ha">Hausa</option><option value="yo">Yorùbá</option><option value="ig">Igbo</option>
          </select>
        </label>
        <label className="field-wide"><span><input type="checkbox" checked={inApp} onChange={event => setInApp(event.target.checked)}/> {t("In-app notifications")}</span></label>
        <label className="field-wide"><span><input type="checkbox" checked={email} onChange={event => setEmail(event.target.checked)}/> {t("Email notification preference")}</span><small className="muted">{t("Email delivery will take effect when an SMTP/email provider is configured for this deployment.")}</small></label>
        <div className="field-wide"><button className="button button-primary" disabled={busy} onClick={() => void save()}>{busy ? t("Saving…") : t("Save preferences")}</button></div>
      </div>
    </>}
    {error && <p className="form-error" role="alert">{error}</p>}
    {notice && <p className="muted" role="status">{notice}</p>}
    <p className="muted" style={{ marginTop: "1rem" }}>{t("Language support is being expanded. Some legal and official content may remain in English until reviewed translations are approved.")}</p>
  </section>;
}
