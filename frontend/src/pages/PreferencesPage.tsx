import { useEffect, useState } from "react";
import { api } from "../services/api";
import { useLanguage, type Language } from "../state/LanguageContext";

export default function PreferencesPage() {
  const { language, setLanguage, t } = useLanguage();
  const [email, setEmail] = useState(true);
  const [inApp, setInApp] = useState(true);
  const [sms, setSms] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState("");
  const [verifiedAt, setVerifiedAt] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [verificationSent, setVerificationSent] = useState(false);
  const [requestingCode, setRequestingCode] = useState(false);
  const [verifyingCode, setVerifyingCode] = useState(false);
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
      setSms(value.sms_notifications);
      setPhoneNumber(value.phone_number ?? "");
      setVerifiedAt(value.phone_verified_at);
      if (!localStorage.getItem("govconnectx_language")) setLanguage(value.preferred_language);
    }).catch(reason => {
      if (active) setError(reason instanceof Error ? reason.message : t("Could not load preferences."));
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [setLanguage, t]);

  async function requestCode() {
    setRequestingCode(true); setError(""); setNotice("");
    try {
      const result = await api.requestPhoneVerification(phoneNumber.trim());
      setVerificationSent(true);
      setVerifiedAt(null);
      setSms(false);
      setCode("");
      setNotice(t("Phone verification code sent."));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t("Could not request phone verification."));
    } finally {
      setRequestingCode(false);
    }
  }

  async function verifyCode() {
    setVerifyingCode(true); setError(""); setNotice("");
    try {
      await api.verifyPhone(code);
      setVerifiedAt(new Date().toISOString());
      setVerificationSent(false);
      setCode("");
      setSms(false);
      setNotice(t("Phone number verified. You can now enable SMS notifications."));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t("Could not verify phone number."));
    } finally {
      setVerifyingCode(false);
    }
  }

  async function save() {
    setBusy(true); setError(""); setNotice("");
    try {
      const saved = await api.updatePreferences({
        email_notifications: email,
        in_app_notifications: inApp,
        sms_notifications: sms,
        preferred_language: language,
      });
      setLanguage(saved.preferred_language);
      setSms(saved.sms_notifications);
      setNotice(t("Your preferences have been saved."));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t("Could not save preferences."));
    } finally {
      setBusy(false);
    }
  }

  const validPhone = /^\+[1-9][0-9]{7,14}$/.test(phoneNumber.trim());
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
        <div className="field-wide">
          <h2>{t("Phone number")}</h2>
          <p className="muted">{t("Enter your phone number in international format, e.g. +2348012345678.")}</p>
          <label>{t("Phone number")}
            <input type="tel" inputMode="tel" autoComplete="tel" maxLength={16} placeholder="+2348012345678" value={phoneNumber}
              onChange={event => { setPhoneNumber(event.target.value); if (event.target.value.trim() !== phoneNumber) setVerifiedAt(null); }} />
          </label>
          <button className="button button-quiet" type="button" disabled={!validPhone || requestingCode || verifiedAt !== null} onClick={() => void requestCode()}>
            {requestingCode ? t("Sending code…") : t("Send verification code")}
          </button>
          {verifiedAt && <p className="muted" role="status">{t("Verified")}</p>}
          {verificationSent && <div className="form-stack">
            <label>{t("Verification code")}
              <input inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} value={code} onChange={event => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))} />
            </label>
            <p className="muted">{t("Enter the 6-digit code sent to your phone.")}</p>
            <button className="button button-quiet" type="button" disabled={code.length !== 6 || verifyingCode} onClick={() => void verifyCode()}>
              {verifyingCode ? t("Verifying…") : t("Verify phone number")}
            </button>
          </div>}
        </div>
        <label className="field-wide"><span><input type="checkbox" checked={sms} disabled={!verifiedAt} onChange={event => setSms(event.target.checked)}/> {t("SMS notifications")}</span>
          <small className="muted">{t("SMS alerts require a verified number and your explicit consent. You can turn them off at any time.")}</small>
        </label>
        <div className="field-wide"><button className="button button-primary" disabled={busy} onClick={() => void save()}>{busy ? t("Saving…") : t("Save preferences")}</button></div>
      </div>
    </>}
    {error && <p className="form-error" role="alert">{error}</p>}
    {notice && <p className="muted" role="status">{notice}</p>}
    <p className="muted" style={{ marginTop: "1rem" }}>{t("Language support is being expanded. Some legal and official content may remain in English until reviewed translations are approved.")}</p>
  </section>;
}
