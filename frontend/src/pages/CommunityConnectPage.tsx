import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import type { GeographicState, LocalGovernmentArea } from "../types/api";

export default function CommunityConnectPage() {
  const [states, setStates] = useState<GeographicState[]>([]);
  const [lgas, setLgas] = useState<LocalGovernmentArea[]>([]);
  const [stateCode, setStateCode] = useState("");
  const [lgaCode, setLgaCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    api.states().then(setStates).catch(() => setError("Could not load the state directory."));
  }, []);

  useEffect(() => {
    setLgaCode("");
    if (!stateCode) { setLgas([]); return; }
    setLoading(true);
    api.lgas(stateCode).then(setLgas).catch(() => setError("Could not load LGAs.")).finally(() => setLoading(false));
  }, [stateCode]);

  useEffect(() => {
    if (!lgaCode) return;
    navigate(`/community-chat/LGA-${encodeURIComponent(lgaCode)}`);
  }, [lgaCode, navigate]);

  return <div className="page-stack">
    <section className="citizen-dashboard-banner">
      <div><p className="eyebrow">COMMUNITY CONNECT</p><h1>Local voices. Shared progress.</h1>
        <p>Choose your State and Local Government Area to enter its shared live community chat.</p></div>
      <span className="dashboard-fist" aria-hidden="true">◎</span>
    </section>
    <section className="panel">
      <div className="panel-heading"><div><h2>Find your community</h2>
        <p className="muted">Only your State and LGA are needed. Live GPS, Ward and Community selection are not required.</p></div></div>
      <div className="form-grid">
        <label>State<select value={stateCode} onChange={event => setStateCode(event.target.value)}>
          <option value="">Select a state</option>{states.map(item => <option key={item.code} value={item.code}>{item.name}</option>)}
        </select></label>
        <label>Local Government Area<select value={lgaCode} onChange={event => setLgaCode(event.target.value)} disabled={!stateCode || loading}>
          <option value="">Select an LGA</option>{lgas.map(item => <option key={item.code} value={item.code}>{item.name}</option>)}
        </select></label>
      </div>
      {loading && <p className="muted" role="status">Loading Local Government Areas…</p>}
      {error && <p className="form-error" role="alert">{error}</p>}
      <p className="muted">Selecting an LGA opens its shared live chat. You can join that room to send messages and photos.</p>
    </section>
  </div>;
}
