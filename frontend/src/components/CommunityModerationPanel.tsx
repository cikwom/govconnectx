import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../services/api";
import { useLanguage } from "../state/LanguageContext";

type Listing = { id: number; listing_type: string; title: string; description: string; location_text: string; contact_instructions: string; moderation_status: string };
export default function CommunityModerationPanel() {
  const { t } = useLanguage();
  const [items, setItems] = useState<Listing[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState<number | null>(null);
  const [name, setName] = useState("");
  const [category, setCategory] = useState("Public service");
  const [description, setDescription] = useState("");
  const [address, setAddress] = useState("");
  const [phone, setPhone] = useState("");

  async function load() {
    try { setItems(await api.adminCommunityListings()); setError(""); }
    catch (reason) { setError(reason instanceof Error ? reason.message : t("Could not load moderation queue.")); }
  }
  useEffect(() => { void load(); }, []);

  async function moderate(id: number, moderation_status: "APPROVED" | "REJECTED") {
    setBusy(id); setError(""); setNotice("");
    try { await api.moderateCommunityListing(id, moderation_status); setNotice(`${t("Listing")} #${id} ${t(moderation_status)}.`); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : t("Moderation failed.")); }
    finally { setBusy(null); }
  }

  async function publishService(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setNotice("");
    try {
      await api.createServiceDirectoryEntry({ name: name.trim(), category: category.trim(), description: description.trim(), address: address.trim(), phone: phone.trim() || undefined });
      setName(""); setDescription(""); setAddress(""); setPhone("");
      setNotice(t("Service directory entry published as verified."));
    } catch (reason) { setError(reason instanceof Error ? reason.message : t("Could not publish service entry.")); }
  }

  return <>
    <section className="panel">
      <div className="panel-heading"><div><h2>{t("Lost and Found moderation")}</h2><p className="muted">{t("Review public notices before publication.")}</p></div><span className="admin-count">{items.length} {t("pending")}</span></div>
      {error && <p className="form-error" role="alert">{error}</p>}
      {notice && <p className="muted" role="status">{notice}</p>}
      {items.length === 0 ? <p className="empty-state">{t("No pending community notices.")}</p> : <div className="report-list">{items.map(item => <article className="report-row" key={item.id}><div className="report-main"><div className="report-title-line"><h3>{item.title}</h3><span className="status-badge">{t(item.listing_type.toUpperCase())}</span></div><p>{item.description}</p><small>{item.location_text} · {t("Contact instructions:")} {item.contact_instructions}</small><div className="form-actions"><button className="button button-primary button-small" disabled={busy === item.id} onClick={() => void moderate(item.id, "APPROVED")}>{t("Approve")}</button><button className="button button-quiet button-small" disabled={busy === item.id} onClick={() => void moderate(item.id, "REJECTED")}>{t("Reject")}</button></div></div></article>)}</div>}
    </section>
    <section className="panel">
      <div className="panel-heading"><div><h2>{t("Publish government service")}</h2><p className="muted">{t("Only publish entries whose details have been checked against an authoritative source.")}</p></div></div>
      <form className="form-grid" onSubmit={publishService}>
        <label>{t("Service name")}<input required minLength={3} value={name} onChange={event => setName(event.target.value)}/></label>
        <label>{t("Category")}<input required value={category} onChange={event => setCategory(event.target.value)}/></label>
        <label className="field-wide">{t("Description")}<textarea required minLength={10} value={description} onChange={event => setDescription(event.target.value)}/></label>
        <label className="field-wide">{t("Office address")}<input required value={address} onChange={event => setAddress(event.target.value)}/></label>
        <label>{t("Public phone (optional)")}<input value={phone} onChange={event => setPhone(event.target.value)}/></label>
        <div className="field-wide"><button className="button button-primary">{t("Publish verified listing")}</button></div>
      </form>
    </section>
  </>;
}
