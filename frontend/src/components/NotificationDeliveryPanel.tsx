import { useCallback, useEffect, useState } from "react";
import { api } from "../services/api";
import { useLanguage } from "../state/LanguageContext";

type DeliveryReport = Awaited<ReturnType<typeof api.adminNotificationDeliveries>>;

export default function NotificationDeliveryPanel() {
  const { t, locale } = useLanguage();
  const [report, setReport] = useState<DeliveryReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setReport(await api.adminNotificationDeliveries());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t("Could not load notification delivery status."));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => { void refresh(); }, [refresh]);

  function formatDate(value: string | null) {
    return value ? new Date(value).toLocaleString(locale) : "—";
  }

  return <section className="panel">
    <div className="panel-heading">
      <div>
        <h2>{t("Notification delivery health")}</h2>
        <p className="muted">{t("Monitor queued, sent and failed email/SMS delivery attempts.")}</p>
      </div>
      <button className="button button-quiet button-small" type="button" onClick={() => void refresh()} disabled={loading}>{t("Refresh delivery status")}</button>
    </div>
    {report && <div className="delivery-summary">
      <div><strong>{report.summary.queued}</strong><span>{t("Queued")}</span></div>
      <div><strong>{report.summary.sending}</strong><span>{t("Sending")}</span></div>
      <div><strong>{report.summary.sent}</strong><span>{t("Sent")}</span></div>
      <div><strong>{report.summary.failed}</strong><span>{t("Failed")}</span></div>
    </div>}
    {loading && <p className="empty-state">{t("Loading…")}</p>}
    {error && <p className="form-error" role="alert">{error}</p>}
    {report && !loading && <div className="admin-table-wrap">
      <table className="admin-table">
        <thead><tr>
          <th>{t("Channel")}</th><th>{t("Destination")}</th><th>{t("Status")}</th>
          <th>{t("Attempts")}</th><th>{t("Next attempt")}</th><th>{t("Created")}</th>
        </tr></thead>
        <tbody>
          {report.items.map(item => <tr key={item.id}>
            <td>{item.channel.toUpperCase()}</td>
            <td>{item.destination}</td>
            <td><span className={`delivery-status delivery-status-${item.status}`}>{t(item.status.charAt(0).toUpperCase() + item.status.slice(1))}</span>{item.last_error && <small>{t(item.last_error)}</small>}</td>
            <td>{item.attempts}/{item.max_attempts}</td>
            <td>{item.status === "queued" ? formatDate(item.next_attempt_at) : "—"}</td>
            <td>{formatDate(item.created_at)}</td>
          </tr>)}
        </tbody>
      </table>
      {report.items.length === 0 && <p className="empty-state">{t("No notification deliveries have been queued.")}</p>}
    </div>}
  </section>;
}
