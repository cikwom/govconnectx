import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../services/api";
import { useAuth } from "../state/AuthContext";
import { useLanguage } from "../state/LanguageContext";

export default function ReportActionPanel({ reportId, status }: { reportId: number; status: string }) {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [duplicateMessage, setDuplicateMessage] = useState("");
  const [reason, setReason] = useState("");
  const [urgency, setUrgency] = useState<"normal" | "high" | "critical">("high");
  const [rating, setRating] = useState(5);
  const [feedback, setFeedback] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    api.duplicateHint(reportId)
      .then(result => { if (active) setDuplicateMessage(result.message); })
      .catch(() => { if (active) setDuplicateMessage(""); });
    return () => { active = false; };
  }, [reportId]);

  async function escalate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try {
      const result = await api.requestEscalation(reportId, urgency, reason.trim());
      setNotice(result.notice); setReason("");
    } catch (reason) { setError(reason instanceof Error ? reason.message : t("Could not request escalation.")); }
    finally { setBusy(false); }
  }

  async function submitFeedback(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try {
      await api.submitReportFeedback(reportId, rating, feedback.trim() || undefined);
      setNotice(t("Thank you. Your feedback has been recorded.")); setFeedback("");
    } catch (reason) { setError(reason instanceof Error ? reason.message : t("Could not submit feedback.")); }
    finally { setBusy(false); }
  }

  return <section className="panel">
    <div className="panel-heading"><div><h2>{t("Report actions")}</h2><p className="muted">{t("Additional ways to support fair review and accountability.")}</p></div></div>
    {duplicateMessage && <p className="muted">{duplicateMessage}</p>}
    {user?.role === "citizen" && <form className="comment-form" onSubmit={escalate}>
      <h3>{t("Request additional attention")}</h3>
      <p className="muted">{t("Use this if the issue has become more urgent or has not received appropriate attention. This alerts platform administrators; it does not dispatch emergency responders.")}</p>
      <label>{t("Urgency")}<select value={urgency} onChange={event => setUrgency(event.target.value as "normal" | "high" | "critical")}><option value="normal">{t("Normal")}</option><option value="high">{t("High")}</option><option value="critical">{t("Critical")}</option></select></label>
      <label>{t("Why does this need attention?")}<textarea rows={3} minLength={10} maxLength={2000} required value={reason} onChange={event => setReason(event.target.value)} placeholder={t("Explain what has changed or why this needs review.")}/></label>
      <button className="button button-quiet" disabled={busy || !reason.trim()}>{busy ? t("Sending…") : t("Request escalation")}</button>
    </form>}
    {user?.role === "citizen" && status === "RESOLVED" && <form className="comment-form" onSubmit={submitFeedback}>
      <h3>{t("How was this issue handled?")}</h3>
      <label>{t("Rating")}<select value={rating} onChange={event => setRating(Number(event.target.value))}><option value={5}>5 – {t("Excellent")}</option><option value={4}>4 – {t("Good")}</option><option value={3}>3 – {t("Fair")}</option><option value={2}>2 – {t("Poor")}</option><option value={1}>1 – {t("Very poor")}</option></select></label>
      <label>{t("Comments (optional)")}<textarea rows={3} maxLength={2000} value={feedback} onChange={event => setFeedback(event.target.value)} placeholder={t("Share feedback about the resolution.")}/></label>
      <button className="button button-primary" disabled={busy}>{t("Submit feedback")}</button>
    </form>}
    {error && <p className="form-error" role="alert">{error}</p>}
    {notice && <p className="muted" role="status">{notice}</p>}
    <p className="muted">{t("If anyone is in immediate danger, contact the appropriate official emergency service directly.")}</p>
  </section>;
}
