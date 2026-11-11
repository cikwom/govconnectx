import { useState } from "react";
import { tokenStore } from "../services/api";
import { useLanguage } from "../state/LanguageContext";

type ImportPreview = {
  total_rows: number;
  valid_rows: number;
  wards: number;
  communities: number;
  errors: { row: number; code: string; error: string }[];
  can_import: boolean;
  notice: string;
};
type ImportResult = { imported: number; wards: number; communities: number; source_name: string; effective_from: string | null };

const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
const CSV_TEMPLATE = "record_type,code,name,parent_code\nward,OFFICIAL-WARD-CODE,Official ward name,OFFICIAL-LGA-CODE\ncommunity,OFFICIAL-COMMUNITY-CODE,Official community name,OFFICIAL-WARD-CODE\n";

export default function GeographicBulkImportPanel() {
  const { t } = useLanguage();
  const [file, setFile] = useState<File | null>(null);
  const [sourceName, setSourceName] = useState("");
  const [sourceReference, setSourceReference] = useState("");
  const [effectiveFrom, setEffectiveFrom] = useState("");
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function clearPreview() { setPreview(null); setResult(null); setError(""); }

  async function submit(mode: "preview" | "commit") {
    if (!file || !sourceName.trim() || !sourceReference.trim()) return;
    setBusy(true); setError(""); setResult(null);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("source_name", sourceName.trim());
      form.append("source_reference", sourceReference.trim());
      if (effectiveFrom) form.append("effective_from", effectiveFrom);
      const response = await fetch(`${API_URL}/api/v1/locations/admin/import/${mode}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${tokenStore.get() ?? ""}` },
        body: form,
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = body.detail;
        if (detail && typeof detail === "object" && Array.isArray(detail.errors)) {
          setPreview(current => current ? { ...current, can_import: false, errors: detail.errors } : current);
          throw new Error(detail.message ?? "Import was rejected. Correct the CSV and preview it again.");
        }
        throw new Error(typeof detail === "string" ? detail : `Request failed (${response.status})`);
      }
      if (mode === "preview") setPreview(body as ImportPreview);
      else { setResult(body as ImportResult); setPreview(null); setFile(null); }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t("Could not process geographic CSV"));
    } finally { setBusy(false); }
  }

  return <section className="panel">
    <div className="panel-heading"><div><p className="eyebrow">{t("AUTHORITATIVE REFERENCE DATA")}</p><h2>{t("Bulk import wards and communities")}</h2>
      <p className="muted">{t("Upload a UTF-8 CSV, validate every parent relationship, preview the result, then explicitly commit. Existing codes are never overwritten.")}</p></div></div>
    <div className="form-grid">
      <label>{t("Source organisation / publisher")}<input required maxLength={180} value={sourceName} onChange={e => { setSourceName(e.target.value); clearPreview(); }} placeholder={t("e.g. INEC or State Government")} /></label>
      <label>{t("Source document / reference")}<input required maxLength={500} value={sourceReference} onChange={e => { setSourceReference(e.target.value); clearPreview(); }} placeholder={t("Official document title or public reference")} /></label>
      <label>{t("Effective date (optional)")}<input type="date" value={effectiveFrom} onChange={e => { setEffectiveFrom(e.target.value); clearPreview(); }} /></label>
      <label>{t("CSV file")}<input type="file" accept=".csv,text/csv" onChange={e => { setFile(e.target.files?.[0] ?? null); clearPreview(); }} /></label>
    </div>
    <div className="form-actions">
      <button type="button" className="button button-quiet button-small" onClick={() => {
        const blob = new Blob([CSV_TEMPLATE], { type: "text/csv;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url; anchor.download = "govconnectx-geography-template.csv"; anchor.click();
        URL.revokeObjectURL(url);
      }}>{t("Download CSV template")}</button>
      <button type="button" className="button button-primary button-small" disabled={busy || !file || !sourceName.trim() || !sourceReference.trim()} onClick={() => void submit("preview")}>{busy ? t("Processing…") : t("Validate and preview")}</button>
    </div>
    <p className="muted">Required columns: <code>record_type,code,name,parent_code</code>. Use <code>ward</code> with an existing LGA code, or <code>community</code> with an existing ward code (a ward may appear earlier in the same file). {t("Maximum 5,000 rows and 2 MB. Use only source data you have independently verified.")}</p>
    {preview && <article className="oversight-item">
      <strong>{t("Import preview")}</strong>
      <p>{preview.valid_rows} {t("valid rows of")} {preview.total_rows} · {preview.wards} {t("wards")} · {preview.communities} {t("communities")}</p>
      {preview.errors.length > 0 && <div role="alert"><strong>{preview.errors.length} {t("issue(s) must be corrected")}</strong><ul>{preview.errors.map((item, index) => <li key={index}>Row {item.row} · {item.code || t("No code")}: {item.error}</li>)}</ul></div>}
      <p className="muted">{preview.notice}</p>
      <button type="button" className="button button-primary button-small" disabled={busy || !preview.can_import} onClick={() => void submit("commit")}>{t("Commit validated import")}</button>
    </article>}
    {result && <p className="geo-success" role="status">{t("Imported")} {result.imported} {t("records:")} {result.wards} {t("wards")} {t("and")} {result.communities} {t("communities")}. {t("Source attribution and import audit record saved.")}</p>}
    {error && <p className="form-error" role="alert">{error}</p>}
  </section>;
}
