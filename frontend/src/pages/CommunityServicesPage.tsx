import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../services/api";
import { useLanguage } from "../state/LanguageContext";

type Listing = { id: number; listing_type: "lost" | "found"; title: string; description: string; location_text: string; contact_instructions: string; created_at: string };
type Service = { id: number; name: string; category: string; description: string; address: string; phone: string | null; website: string | null; is_verified: boolean };

export default function CommunityServicesPage() {
  const { t } = useLanguage();
  const [listings, setListings] = useState<Listing[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [kind, setKind] = useState<"lost" | "found">("lost");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [contact, setContact] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    setError("");
    try {
      const [items, directory] = await Promise.all([api.communityListings(), api.publicServiceDirectory()]);
      setListings(items);
      setServices(directory);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load community services.");
    } finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true); setError(""); setNotice("");
    try {
      await api.createCommunityListing({ listing_type: kind, title: title.trim(), description: description.trim(), location_text: location.trim(), contact_instructions: contact.trim() });
      setTitle(""); setDescription(""); setLocation(""); setContact("");
      setNotice("Your listing has been submitted for administrator review. It will appear publicly after approval.");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not submit listing.");
    } finally { setBusy(false); }
  }

  return <>
    <section className="welcome-row"><div><p className="eyebrow">COMMUNITY SERVICES</p><h1>{t("Community help centre")}</h1><p className="muted">Find public services and share Lost and Found notices with your community.</p></div></section>
    {error && <p className="form-error" role="alert">{error}</p>}
    {notice && <p className="success-message" role="status">{notice}</p>}
    <section className="panel">
      <div className="panel-heading"><div><h2>{t("Lost and Found")}</h2><p className="muted">Listings are reviewed before publication. Do not post passwords, bank details, identity numbers or sensitive personal information.</p></div></div>
      <form className="form-grid" onSubmit={submit}>
        <label>Listing type<select value={kind} onChange={event => setKind(event.target.value as "lost" | "found")}><option value="lost">I lost something</option><option value="found">I found something</option></select></label>
        <label>Item or notice title<input required minLength={4} maxLength={180} value={title} onChange={event => setTitle(event.target.value)} placeholder="e.g. Black backpack"/></label>
        <label className="field-wide">Description<textarea required minLength={10} maxLength={3000} rows={3} value={description} onChange={event => setDescription(event.target.value)} placeholder="Describe the item without including sensitive personal details."/></label>
        <label>Where was it lost or found?<input required value={location} onChange={event => setLocation(event.target.value)} maxLength={300} placeholder="Town, area or public landmark"/></label>
        <label>Safe contact instructions<input required value={contact} onChange={event => setContact(event.target.value)} maxLength={500} placeholder="e.g. Contact through the platform"/></label>
        <div className="field-wide"><button className="button button-primary" disabled={busy}>{busy ? "Submitting…" : "Submit for review"}</button></div>
      </form>
    </section>
    <section className="panel">
      <div className="panel-heading"><div><h2>Community notices</h2><p className="muted">Only listings approved by a platform administrator appear here.</p></div><button className="button button-quiet button-small" onClick={() => void load()}>Refresh</button></div>
      {loading ? <p className="empty-state">Loading notices…</p> : listings.length === 0 ? <p className="empty-state">No approved Lost and Found notices yet.</p> : <div className="report-list">{listings.map(item => <article className="report-row" key={item.id}><div className="report-symbol">{item.listing_type === "lost" ? "?" : "✓"}</div><div className="report-main"><div className="report-title-line"><h3>{item.title}</h3><span className="status-badge">{item.listing_type.toUpperCase()}</span></div><p>{item.description}</p><small>{item.location_text} · {new Intl.DateTimeFormat("en-NG", { dateStyle: "medium" }).format(new Date(item.created_at))}</small><p><strong>Contact:</strong> {item.contact_instructions}</p></div></article>)}</div>}
    </section>
    <section className="panel">
      <div className="panel-heading"><div><h2>{t("Government service directory")}</h2><p className="muted">Public service listings verified by GovConnectX administrators.</p></div></div>
      {loading ? <p className="empty-state">Loading directory…</p> : services.length === 0 ? <p className="empty-state">The verified service directory is being prepared.</p> : <div className="report-list">{services.map(service => <article className="report-row" key={service.id}><div className="report-symbol">i</div><div className="report-main"><div className="report-title-line"><h3>{service.name}</h3><span className="status-badge">VERIFIED</span></div><p>{service.category} · {service.description}</p><small>{service.address}{service.phone ? ` · ${service.phone}` : ""}</small>{service.website && <p><a href={service.website} target="_blank" rel="noreferrer">Official website ↗</a></p>}</div></article>)}</div>}
    </section>
  </>;
}
