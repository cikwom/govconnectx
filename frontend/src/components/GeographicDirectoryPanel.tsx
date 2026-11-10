import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../services/api";
import type { Community, GeographicState, GeographicWard, LocalGovernmentArea } from "../types/api";

export default function GeographicDirectoryPanel() {
  const [states, setStates] = useState<GeographicState[]>([]);
  const [lgas, setLgas] = useState<LocalGovernmentArea[]>([]);
  const [wards, setWards] = useState<GeographicWard[]>([]);
  const [stateCode, setStateCode] = useState("");
  const [lgaCode, setLgaCode] = useState("");
  const [wardCode, setWardCode] = useState("");
  const [newWardCode, setNewWardCode] = useState("");
  const [wardName, setWardName] = useState("");
  const [communityCode, setCommunityCode] = useState("");
  const [communityName, setCommunityName] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.states().then(setStates).catch(() => setError("Could not load states.")); }, []);
  useEffect(() => { setLgaCode(""); setWardCode(""); setWards([]); if (!stateCode) { setLgas([]); return; } api.lgas(stateCode).then(setLgas).catch(() => setError("Could not load LGAs.")); }, [stateCode]);
  useEffect(() => { setWardCode(""); if (!lgaCode) { setWards([]); return; } api.wards(lgaCode).then(setWards).catch(() => setError("Could not load wards.")); }, [lgaCode]);

  async function addWard(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try {
      await api.createWard({ code: newWardCode.trim().toUpperCase(), name: wardName.trim(), lga_code: lgaCode });
      setNewWardCode(""); setWardName(""); setNotice("Ward added to the geographic directory.");
      setWards(await api.wards(lgaCode));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not add ward."); }
    finally { setBusy(false); }
  }
  async function addCommunity(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try {
      await api.createCommunity({ code: communityCode.trim().toUpperCase(), name: communityName.trim(), ward_code: wardCode });
      setCommunityCode(""); setCommunityName(""); setNotice("Community added to the geographic directory.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not add community."); }
    finally { setBusy(false); }
  }

  return <section className="panel">
    <div className="panel-heading"><div><p className="eyebrow">GEOGRAPHIC DIRECTORY</p><h2>Wards and communities</h2><p className="muted">Add verified ward and community reference data. Do not invent boundaries or codes; use authoritative state/INEC records.</p></div></div>
    <div className="form-grid">
      <label>State<select value={stateCode} onChange={event => setStateCode(event.target.value)}><option value="">Select state</option>{states.map(item => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
      <label>LGA<select value={lgaCode} disabled={!stateCode} onChange={event => setLgaCode(event.target.value)}><option value="">Select LGA</option>{lgas.map(item => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
    </div>
    <form className="form-grid" onSubmit={addWard} style={{ marginTop: "1rem" }}>
      <label>Ward code<input required minLength={2} maxLength={24} value={newWardCode} onChange={event => setNewWardCode(event.target.value)} placeholder="Official ward code"/></label>
      <label>Ward name<input required minLength={2} maxLength={150} value={wardName} onChange={event => setWardName(event.target.value)} placeholder="Ward name"/></label>
      <div className="field-wide"><button className="button button-primary" disabled={busy || !lgaCode || !newWardCode.trim()}>Add ward</button></div>
    </form>
    <div className="form-grid" style={{ marginTop: "1rem" }}>
      <label>Existing ward<select value={wardCode} onChange={event => setWardCode(event.target.value)} disabled={!lgaCode}><option value="">Select ward</option>{wards.map(item => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
    </div>
    <form className="form-grid" onSubmit={addCommunity}>
      <label>Community code<input required minLength={2} maxLength={32} value={communityCode} onChange={event => setCommunityCode(event.target.value)} placeholder="Official community code"/></label>
      <label>Community name<input required minLength={2} maxLength={180} value={communityName} onChange={event => setCommunityName(event.target.value)} placeholder="Community name"/></label>
      <div className="field-wide"><button className="button button-quiet" disabled={busy || !wardCode || !wards.some(item => item.code === wardCode)}>Add community</button></div>
    </form>
    {error && <p className="form-error" role="alert">{error}</p>}
    {notice && <p className="muted" role="status">{notice}</p>}
  </section>;
}
