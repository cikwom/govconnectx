import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import type { GeographicState, LocalGovernmentArea } from "../types/api";

export default function CommunityConnectPage() {
  const [states, setStates] = useState<GeographicState[]>([]);
  const [lgas, setLgas] = useState<LocalGovernmentArea[]>([]);
  const [stateCode, setStateCode] = useState("");
  const [query, setQuery] = useState("");
  const [loadingStates, setLoadingStates] = useState(true);
  const [loadingLgas, setLoadingLgas] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    let active = true;
    api.states().then(items => { if (active) setStates(items); })
      .catch(() => { if (active) setError("We could not load the state directory. Please refresh and try again."); })
      .finally(() => { if (active) setLoadingStates(false); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    setLgas([]);
    if (!stateCode) { setLoadingLgas(false); return () => { active = false; }; }
    setLoadingLgas(true);
    setError("");
    api.lgas(stateCode).then(items => { if (active) setLgas(items); })
      .catch(() => { if (active) setError("We could not load LGAs for this state. Please try selecting the state again."); })
      .finally(() => { if (active) setLoadingLgas(false); });
    return () => { active = false; };
  }, [stateCode]);

  const selectedState = states.find(item => item.code === stateCode);
  const visibleLgas = useMemo(() => lgas.filter(item => item.name.toLowerCase().includes(query.trim().toLowerCase())), [lgas, query]);

  return <main className="page-stack x-community">
    <header className="x-community-header">
      <div><p className="eyebrow">GOVCONNECTX COMMUNITIES</p><h1>What's happening in your community?</h1><p>Follow local conversations, share useful updates and help your neighbours stay informed.</p></div>
      <span className="x-community-mark" aria-hidden="true">G<span>×</span></span>
    </header>

    <div className="x-community-layout">
      <section className="x-community-main" aria-label="Community directory">
        <div className="x-community-tabs"><span className="active">Explore communities</span><span>State and LGA spaces</span></div>
        <section className="x-community-picker">
          <label htmlFor="community-state">Choose a state</label>
          <select id="community-state" value={stateCode} disabled={loadingStates} onChange={event => { setStateCode(event.target.value); setQuery(""); }}>
            <option value="">{loadingStates ? "Loading states…" : "Select a state"}</option>
            {states.map(item => <option key={item.code} value={item.code}>{item.name}</option>)}
          </select>
          <p className="muted">Choose a state to discover its Local Government Area communities. You do not need to share live GPS location.</p>
        </section>
        {error && <p className="form-error" role="alert">{error}</p>}
        {!stateCode && <div className="x-community-empty"><span className="x-empty-icon">⌖</span><h2>Find your people</h2><p>Select your state to see its LGA discussion spaces and join conversations happening nearby.</p></div>}
        {stateCode && <section className="x-lga-section">
          <div className="x-section-heading"><div><p className="eyebrow">STATE COMMUNITY</p><h2>{selectedState?.name}</h2><p className="muted">Choose an LGA to open its live group conversation.</p></div><span className="x-count">{lgas.length} LGAs</span></div>
          <label className="x-search-label" htmlFor="lga-search">Search Local Government Areas</label>
          <input id="lga-search" type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Search by LGA name…" />
          {loadingLgas ? <p className="muted" role="status">Loading LGA communities…</p> : visibleLgas.length ? <div className="x-lga-list">{visibleLgas.map(lga => <button className="x-lga-card" type="button" key={lga.code} onClick={() => navigate(`/community-chat/LGA-${encodeURIComponent(lga.code)}`)}>
            <span className="x-lga-avatar">{lga.name.slice(0, 1).toUpperCase()}</span><span className="x-lga-copy"><strong>{lga.name}</strong><small>{selectedState?.name} · LGA community</small></span><span className="x-lga-open">Open discussion <b>→</b></span>
          </button>)}</div> : <p className="muted">No LGAs match that search.</p>}
        </section>}
      </section>

      <aside className="x-community-sidebar">
        <section className="x-sidebar-card"><h2>Community guidelines</h2><p>Keep discussions respectful, factual and useful. Do not post private information or unverified accusations.</p><ul><li>Respect your neighbours</li><li>Share helpful local information</li><li>Report harmful or misleading content</li></ul></section>
        <section className="x-sidebar-card x-sidebar-highlight"><span className="eyebrow">LOCAL VOICES</span><h2>Small updates can make a difference.</h2><p>Use your LGA space to discuss local concerns, share photos and coordinate with neighbours.</p></section>
      </aside>
    </div>
  </main>;
}
