import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../services/api";
import type { Community, CommunityPost, CommunityPostComment, GeographicState, GeographicWard, LocalGovernmentArea } from "../types/api";
import { useAuth } from "../state/AuthContext";

const staffRoles = ["official", "department_admin", "supervisor", "system_admin"];

export default function CommunityConnectPage() {
  const { user } = useAuth();
  const [states, setStates] = useState<GeographicState[]>([]);
  const [lgas, setLgas] = useState<LocalGovernmentArea[]>([]);
  const [wards, setWards] = useState<GeographicWard[]>([]);
  const [communities, setCommunities] = useState<Community[]>([]);
  const [stateCode, setStateCode] = useState("");
  const [lgaCode, setLgaCode] = useState("");
  const [wardCode, setWardCode] = useState("");
  const [communityCode, setCommunityCode] = useState("");
  const [posts, setPosts] = useState<CommunityPost[]>([]);
  const [comments, setComments] = useState<Record<number, CommunityPostComment[]>>({});
  const [expandedPost, setExpandedPost] = useState<number | null>(null);
  const [draft, setDraft] = useState("");
  const [commentDraft, setCommentDraft] = useState("");
  const [announcement, setAnnouncement] = useState(false);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => { api.states().then(setStates).catch(() => setError("Could not load the state directory.")); }, []);
  useEffect(() => {
    setLgaCode(""); setWardCode(""); setCommunityCode(""); setWards([]); setCommunities([]); setPosts([]);
    if (stateCode) api.lgas(stateCode).then(setLgas).catch(() => setError("Could not load LGAs."));
    else setLgas([]);
  }, [stateCode]);
  useEffect(() => {
    setWardCode(""); setCommunityCode(""); setCommunities([]); setPosts([]);
    if (lgaCode) api.wards(lgaCode).then(setWards).catch(() => setError("Could not load wards."));
    else setWards([]);
  }, [lgaCode]);
  useEffect(() => {
    setCommunityCode(""); setPosts([]);
    if (wardCode) api.communities(wardCode).then(setCommunities).catch(() => setError("Could not load communities."));
    else setCommunities([]);
  }, [wardCode]);
  useEffect(() => {
    if (!communityCode) { setPosts([]); return; }
    setLoading(true); setError("");
    api.communityPosts(communityCode).then(setPosts).catch(reason => setError(reason instanceof Error ? reason.message : "Could not load community discussions.")).finally(() => setLoading(false));
  }, [communityCode]);

  async function publish(event: FormEvent) {
    event.preventDefault();
    if (!communityCode || !draft.trim()) return;
    setBusy(true); setError(""); setNotice("");
    try {
      await api.createCommunityPost(communityCode, draft.trim(), announcement);
      setDraft(""); setAnnouncement(false);
      setPosts(await api.communityPosts(communityCode));
      setNotice("Your message has been shared with this community.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not publish your message."); }
    finally { setBusy(false); }
  }

  async function toggleComments(postId: number) {
    if (expandedPost === postId) { setExpandedPost(null); return; }
    setExpandedPost(postId); setCommentDraft(""); setError("");
    try { const loaded = await api.communityPostComments(postId); setComments(current => ({ ...current, [postId]: loaded })); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load comments."); }
  }

  async function submitComment(event: FormEvent, postId: number) {
    event.preventDefault();
    if (!commentDraft.trim()) return;
    setBusy(true); setError("");
    try {
      await api.addCommunityPostComment(postId, commentDraft.trim());
      setCommentDraft("");
      const refreshed = await api.communityPostComments(postId);
      setComments(current => ({ ...current, [postId]: refreshed }));
      setPosts(current => current.map(post => post.id === postId ? { ...post, comment_count: refreshed.length } : post));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not add your comment."); }
    finally { setBusy(false); }
  }

  return <div className="page-stack">
    <section className="citizen-dashboard-banner">
      <div><p className="eyebrow">COMMUNITY CONNECT</p><h1>Local voices. Shared progress.</h1><p>Choose your community to read local conversations, share updates and help neighbours understand what is happening.</p></div>
      <span className="dashboard-fist" aria-hidden="true">◎</span>
    </section>
    <section className="panel">
      <div className="panel-heading"><div><h2>Find your community</h2><p className="muted">Choose your location manually. Live GPS is not required.</p></div></div>
      <div className="form-grid">
        <label>State<select value={stateCode} onChange={e => setStateCode(e.target.value)}><option value="">Select a state</option>{states.map(item => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
        <label>Local Government Area<select value={lgaCode} onChange={e => setLgaCode(e.target.value)} disabled={!stateCode}><option value="">Select an LGA</option>{lgas.map(item => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
        <label>Ward<select value={wardCode} onChange={e => setWardCode(e.target.value)} disabled={!lgaCode}><option value="">Select a ward</option>{wards.map(item => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
        <label>Community<select value={communityCode} onChange={e => setCommunityCode(e.target.value)} disabled={!wardCode}><option value="">Select a community</option>{communities.map(item => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
      </div>
      {communities.length === 0 && wardCode && <p className="muted">No community directory entries are available for this ward yet. Community names must come from verified local records.</p>}
    </section>
    {error && <p className="form-error" role="alert">{error}</p>}
    {notice && <p className="muted" role="status">{notice}</p>}
    {communityCode && <>
      <section className="panel">
        <div className="panel-heading"><div><p className="eyebrow">COMMUNITY SPACE</p><h2>{communities.find(item => item.code === communityCode)?.name ?? "Community discussion"}</h2><p className="muted">A shared space for local conversations and useful updates.</p></div><span className="admin-count">{posts.length} posts</span></div>
        <form className="form-grid" onSubmit={publish}>
          <label className="field-wide">Share an update<textarea required minLength={1} maxLength={5000} rows={4} value={draft} onChange={e => setDraft(e.target.value)} placeholder="What is happening in your community? Add useful details and be respectful."/></label>
          {staffRoles.includes(user?.role ?? "") && <label className="field-wide checkbox-row"><input type="checkbox" checked={announcement} onChange={e => setAnnouncement(e.target.checked)}/> Publish as an official announcement</label>}
          <div className="field-wide form-actions"><button className="button button-primary" disabled={busy || !draft.trim()}>{busy ? "Publishing…" : "Share with community"}</button></div>
        </form>
      </section>
      <section className="panel">
        <div className="panel-heading"><div><h2>Community discussions</h2><p className="muted">Announcements appear before the latest conversations.</p></div><button className="button button-quiet button-small" onClick={() => api.communityPosts(communityCode).then(setPosts).catch(() => setError("Could not refresh posts."))}>Refresh</button></div>
        {loading ? <div className="empty-state">Loading community discussions…</div> : posts.length === 0 ? <div className="empty-state"><h3>Be the first to start a conversation</h3><p>Share a helpful update or describe an issue affecting this community.</p></div> :
          <div className="report-list">{posts.map(post => <article className="report-row" key={post.id}>
            <div className="report-main">
              <div className="report-title-line"><h3>{post.author.full_name}</h3>{post.is_announcement && <span className="status-badge">OFFICIAL ANNOUNCEMENT</span>}</div>
              <p style={{ whiteSpace: "pre-wrap" }}>{post.body}</p>
              <small>{new Date(post.created_at).toLocaleString()}</small>
              <div className="form-actions"><button className="button button-quiet button-small" type="button" onClick={() => void toggleComments(post.id)}>{expandedPost === post.id ? "Hide comments" : "Comments (" + post.comment_count + ")"}</button></div>
              {expandedPost === post.id && <div className="community-comments">
                {(comments[post.id] ?? []).map(comment => <div className="comment-row" key={comment.id}><strong>{comment.author.full_name}</strong><p>{comment.body}</p><small>{new Date(comment.created_at).toLocaleString()}</small></div>)}
                <form className="form-actions" onSubmit={event => void submitComment(event, post.id)}><input aria-label="Write a comment" value={commentDraft} onChange={e => setCommentDraft(e.target.value)} maxLength={2000} placeholder="Write a respectful comment…"/><button className="button button-primary button-small" disabled={busy || !commentDraft.trim()}>Comment</button></form>
              </div>}
            </div>
          </article>)}</div>}
      </section>
    </>}
  </div>;
}
