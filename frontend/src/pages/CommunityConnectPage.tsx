import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import type { GeographicState, LocalGovernmentArea, PublicCommunityFeedPost } from "../types/api";

export default function CommunityConnectPage() {
  const [states, setStates] = useState<GeographicState[]>([]);
  const [lgas, setLgas] = useState<LocalGovernmentArea[]>([]);
  const [stateCode, setStateCode] = useState("");
  const [lgaCode, setLgaCode] = useState("");
  const [query, setQuery] = useState("");
  const [posts, setPosts] = useState<PublicCommunityFeedPost[]>([]);
  const [loadingStates, setLoadingStates] = useState(true);
  const [loadingLgas, setLoadingLgas] = useState(false);
  const [loadingFeed, setLoadingFeed] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    api.states().then(items => { if (active) { setStates(items); if (items.length) setStateCode(items[0].code); } })
      .catch(() => { if (active) setError("We could not load the state directory. Please refresh and try again."); })
      .finally(() => { if (active) setLoadingStates(false); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    setLgas([]);
    setLgaCode("");
    if (!stateCode) { setLoadingLgas(false); return () => { active = false; }; }
    setLoadingLgas(true);
    api.lgas(stateCode).then(items => { if (active) setLgas(items); })
      .catch(() => { if (active) setError("We could not load LGAs for this state."); })
      .finally(() => { if (active) setLoadingLgas(false); });
    return () => { active = false; };
  }, [stateCode]);

  useEffect(() => {
    let active = true;
    if (!stateCode) { setPosts([]); return () => { active = false; }; }
    setLoadingFeed(true);
    setError("");
    api.publicCommunityFeed(stateCode, lgaCode || undefined)
      .then(items => { if (active) setPosts(items); })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : "The public feed could not be loaded."); })
      .finally(() => { if (active) setLoadingFeed(false); });
    return () => { active = false; };
  }, [stateCode, lgaCode]);

  const selectedState = states.find(item => item.code === stateCode);
  const visibleLgas = useMemo(() => lgas.filter(item => item.name.toLowerCase().includes(query.trim().toLowerCase())), [lgas, query]);

  return <main className="page-stack x-community">
    <header className="x-community-header">
      <div><p className="eyebrow">GOVCONNECTX · COMMUNITY CONNECT</p><h1>What's happening around you?</h1><p>Explore public updates and local conversations across Nigerian states and LGAs. Reading the feed does not require joining a chat.</p></div>
      <span className="x-community-mark" aria-hidden="true">G<span>×</span></span>
    </header>
    <div className="x-community-layout">
      <section className="x-community-main" aria-label="Public community feed">
        <div className="x-community-tabs"><button type="button" className={!lgaCode ? "active" : ""} onClick={() => setLgaCode("")}>State feed</button><button type="button" className={lgaCode ? "active" : ""} disabled={!lgaCode} onClick={() => setLgaCode(lgaCode)}>LGA feed</button></div>
        <section className="x-community-picker">
          <label htmlFor="community-state">Choose a state</label>
          <select id="community-state" value={stateCode} disabled={loadingStates} onChange={event => setStateCode(event.target.value)}>
            <option value="">{loadingStates ? "Loading states…" : "Select a state"}</option>
            {states.map(item => <option key={item.code} value={item.code}>{item.name}</option>)}
          </select>
          <p className="muted">Browse without sharing live GPS location or joining a group chat.</p>
        </section>
        {error && <p className="form-error" role="alert">{error}</p>}
        {stateCode && <section className="x-lga-section">
          <div className="x-section-heading"><div><p className="eyebrow">{lgaCode ? "LOCAL GOVERNMENT AREA FEED" : "STATEWIDE PUBLIC FEED"}</p><h2>{lgaCode ? lgas.find(item => item.code === lgaCode)?.name : selectedState?.name}</h2><p className="muted">Public posts from communities in {lgaCode ? "this LGA" : "this state"}.</p></div><span className="x-count">{lgaCode ? "LGA" : lgas.length + " LGAs"}</span></div>
          <label className="x-search-label" htmlFor="lga-search">Find an LGA feed</label>
          <input id="lga-search" type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Search Local Government Areas…" />
          {loadingLgas ? <p className="muted">Loading LGAs…</p> : <div className="x-lga-list">{visibleLgas.map(lga => <button className={lga.code === lgaCode ? "x-lga-card selected" : "x-lga-card"} type="button" key={lga.code} onClick={() => setLgaCode(lga.code)}>
            <span className="x-lga-avatar">{lga.name.slice(0, 1).toUpperCase()}</span><span className="x-lga-copy"><strong>{lga.name}</strong><small>{selectedState?.name} · Public feed</small></span><span className="x-lga-open">{lga.code === lgaCode ? "Viewing feed" : "View feed"} <b>→</b></span>
          </button>)}</div>}
        </section>}
        <section className="x-public-feed" aria-label="Public posts" aria-live="polite">
          <div className="x-feed-heading"><h2>{lgaCode ? "LGA conversations" : "Latest across the state"}</h2><span>{posts.length} posts</span></div>
          {loadingFeed ? <p className="muted">Loading public posts…</p> : posts.length ? posts.map(post => <article className="x-feed-post" key={post.id}>
            <div className="x-feed-avatar">{post.author.full_name.slice(0, 1).toUpperCase()}</div><div className="x-feed-post-body">
              <div className="x-feed-meta"><strong>{post.author.full_name}</strong><span>{post.lga_name} · {new Date(post.created_at).toLocaleString()}</span></div>
              {post.is_announcement && <span className="x-announcement-label">Official announcement</span>}
              <p>{post.body}</p>
              <div className="x-feed-actions"><span>◯ {post.comment_count} comments</span><span>Public discussion</span></div>
            </div>
          </article>) : <div className="x-feed-empty"><strong>No public posts here yet</strong><p>When neighbours share updates in this area, they will appear here. You can still explore other LGAs.</p></div>}
        </section>
      </section>
      <aside className="x-community-sidebar">
        <section className="x-sidebar-card"><h2>Explore openly</h2><p>Read public community updates without joining a live chat. Chat participation stays optional and separate.</p><ul><li>Choose a State or LGA</li><li>Read local announcements</li><li>Follow public conversations</li></ul></section>
        <section className="x-sidebar-card x-sidebar-highlight"><span className="eyebrow">LOCAL VOICES</span><h2>Every neighbourhood has a story.</h2><p>Stay informed about what is happening across your state and local government area.</p><Link to="/community-services">Explore community services →</Link></section>
      </aside>
    </div>
  </main>;
}
