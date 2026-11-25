import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api, tokenStore } from "../services/api";
import type { Community, CommunityPost, CommunityPostAttachment, CommunityPostComment, CommunityPostImage, GeographicState, GeographicWard, LocalGovernmentArea } from "../types/api";
import { useAuth } from "../state/AuthContext";
import { Link } from "react-router-dom";

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
  const [images, setImages] = useState<Record<number, { id: number; filename: string; url: string }[]>>({});
  const [attachments, setAttachments] = useState<Record<number, { id: number; filename: string; contentType: string; url: string }[]>>({});
  const [isMember, setIsMember] = useState(false);
  const [membershipLoading, setMembershipLoading] = useState(false);
  const [liveConnected, setLiveConnected] = useState(false);
  const [socketRetry, setSocketRetry] = useState(0);
  const [conversionPostId, setConversionPostId] = useState<number | null>(null);
  const [conversionTitle, setConversionTitle] = useState("");
  const [conversionCategory, setConversionCategory] = useState("Infrastructure");
  const [conversionAddress, setConversionAddress] = useState("");
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
    let active = true;
    const objectUrls: string[] = [];
    async function loadEvidence() {
      const imageGroups: Record<number, { id: number; filename: string; url: string }[]> = {};
      const attachmentGroups: Record<number, { id: number; filename: string; contentType: string; url: string }[]> = {};
      if (isMember) await Promise.all(posts.map(async post => {
        try {
          const records: CommunityPostImage[] = await api.communityPostImages(post.id);
          imageGroups[post.id] = await Promise.all(records.map(async record => {
            const blob = await api.downloadCommunityPostImage(post.id, record.id);
            const url = URL.createObjectURL(blob); objectUrls.push(url);
            return { id: record.id, filename: record.original_filename, url };
          }));
        } catch { imageGroups[post.id] = []; }
        try {
          const records: CommunityPostAttachment[] = await api.communityPostAttachments(post.id);
          attachmentGroups[post.id] = await Promise.all(records.map(async record => {
            const blob = await api.downloadCommunityPostAttachment(post.id, record.id);
            const url = URL.createObjectURL(blob); objectUrls.push(url);
            return { id: record.id, filename: record.original_filename, contentType: record.content_type, url };
          }));
        } catch { attachmentGroups[post.id] = []; }
      }));
      if (active) { setImages(imageGroups); setAttachments(attachmentGroups); }
      else objectUrls.forEach(URL.revokeObjectURL);
    }
    void loadEvidence();
    return () => { active = false; objectUrls.forEach(URL.revokeObjectURL); };
  }, [posts, isMember]);

  useEffect(() => {
    if (!communityCode) { setPosts([]); setIsMember(false); return; }
    setLoading(true); setMembershipLoading(true); setError("");
    api.communityPosts(communityCode).then(setPosts).catch(reason => setError(reason instanceof Error ? reason.message : "Could not load community discussions.")).finally(() => setLoading(false));
    api.communityMembership(communityCode).then(result => setIsMember(result.is_member)).catch(reason => setError(reason instanceof Error ? reason.message : "Could not check community membership.")).finally(() => setMembershipLoading(false));
  }, [communityCode]);

  useEffect(() => {
    if (!communityCode || !isMember) { setLiveConnected(false); return; }
    let disposed = false;
    let retryTimer: number | undefined;
    const socket = api.openCommunitySocket(communityCode);
    socket.onopen = () => {
      const token = tokenStore.get();
      if (!token) { socket.close(); return; }
      socket.send(JSON.stringify({ type: "authenticate", token }));
    };
    socket.onmessage = event => {
      try {
        const message = JSON.parse(String(event.data)) as { type?: string };
        if (message.type === "connected") { setLiveConnected(true); return; }
        if (message.type === "pong") return;
        api.communityPosts(communityCode).then(setPosts).catch(() => undefined);
      } catch { /* Ignore malformed live events and retain the polling fallback. */ }
    };
    socket.onclose = () => {
      if (!disposed) {
        setLiveConnected(false);
        retryTimer = window.setTimeout(() => setSocketRetry(value => value + 1), 5000);
      }
    };
    socket.onerror = () => { if (!disposed) setLiveConnected(false); };
    const heartbeat = window.setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) socket.send("ping");
    }, 25000);
    return () => {
      disposed = true;
      window.clearInterval(heartbeat);
      if (retryTimer !== undefined) window.clearTimeout(retryTimer);
      socket.close();
    };
  }, [communityCode, isMember, socketRetry]);

  useEffect(() => {
    if (!communityCode || liveConnected) return;
    const timer = window.setInterval(() => {
      api.communityPosts(communityCode).then(setPosts).catch(() => undefined);
    }, 20000);
    return () => window.clearInterval(timer);
  }, [communityCode, liveConnected]);

  async function joinCommunity() {
    setBusy(true); setError("");
    try { await api.joinCommunity(communityCode); setIsMember(true); setNotice("You joined this community. You can now post, comment and share evidence."); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not join this community."); }
    finally { setBusy(false); }
  }

  async function leaveCommunity() {
    setBusy(true); setError("");
    try { await api.leaveCommunity(communityCode); setIsMember(false); setImages({}); setAttachments({}); setNotice("You left this community. You can still read its public discussion feed."); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not leave this community."); }
    finally { setBusy(false); }
  }

  async function uploadVideo(postId: number, file: File) {
    setBusy(true); setError(""); setNotice("");
    try {
      await api.uploadCommunityPostAttachment(postId, file);
      setNotice("Video attached privately to the community discussion.");
      setPosts(await api.communityPosts(communityCode));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not upload the video."); }
    finally { setBusy(false); }
  }

  async function convertPost(event: FormEvent, postId: number) {
    event.preventDefault();
    if (!conversionCategory.trim() || !conversionAddress.trim()) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const result = await api.convertCommunityPostToReport(postId, {
        title: conversionTitle.trim() || undefined,
        category: conversionCategory.trim(),
        address: conversionAddress.trim(),
      });
      setConversionPostId(null); setConversionTitle(""); setConversionAddress("");
      setPosts(await api.communityPosts(communityCode));
      setNotice("Community discussion submitted as official report #" + result.report_id + ".");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not convert this discussion into a report."); }
    finally { setBusy(false); }
  }

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

  async function uploadImage(postId: number, file: File) {
    setBusy(true); setError(""); setNotice("");
    try {
      await api.uploadCommunityPostImage(postId, file);
      setNotice("Photo attached. It is only available to signed-in community members.");
      setPosts(await api.communityPosts(communityCode));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not upload the photo."); }
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
        <div className="panel-heading"><div><p className="eyebrow">COMMUNITY SPACE</p><h2>{communities.find(item => item.code === communityCode)?.name ?? "Community discussion"}</h2><p className="muted">A shared space for local conversations and useful updates.</p><Link className="button button-primary button-small" to={`/community-chat/${encodeURIComponent(communityCode)}`}>Open community group chat</Link></div><span className="admin-count">{posts.length} posts</span></div>
        {membershipLoading ? <p className="muted">Checking membership…</p> : isMember ? <>
          <form className="form-grid" onSubmit={publish}>
            <label className="field-wide">Share an update<textarea required minLength={1} maxLength={5000} rows={4} value={draft} onChange={e => setDraft(e.target.value)} placeholder="What is happening in your community? Add useful details and be respectful."/></label>
            {staffRoles.includes(user?.role ?? "") && <label className="field-wide checkbox-row"><input type="checkbox" checked={announcement} onChange={e => setAnnouncement(e.target.checked)}/> Publish as an official announcement</label>}
            <div className="field-wide form-actions"><button className="button button-primary" disabled={busy || !draft.trim()}>{busy ? "Publishing…" : "Share with community"}</button></div>
          </form>
          <div className="form-actions"><button type="button" className="button button-quiet button-small" disabled={busy} onClick={() => void leaveCommunity()}>Leave community</button></div>
        </> : <div className="empty-state"><h3>Join this community</h3><p>Join to publish messages, comment and share evidence. You can still read the discussion feed without joining.</p><button className="button button-primary" disabled={busy} onClick={() => void joinCommunity()}>{busy ? "Please wait…" : "Join community"}</button></div>}
      </section>
      <section className="panel">
        <div className="panel-heading"><div><h2>Community discussions</h2><p className="muted">Announcements appear before the latest conversations. {liveConnected ? "Live updates are connected." : "Automatic refresh checks for new messages every 20 seconds while reconnecting."}</p></div><button className="button button-quiet button-small" onClick={() => api.communityPosts(communityCode).then(setPosts).catch(() => setError("Could not refresh posts."))}>Refresh</button></div>
        {loading ? <div className="empty-state">Loading community discussions…</div> : posts.length === 0 ? <div className="empty-state"><h3>Be the first to start a conversation</h3><p>Share a helpful update or describe an issue affecting this community.</p></div> :
          <div className="report-list">{posts.map(post => <article className="report-row" key={post.id}>
            <div className="report-main">
              <div className="report-title-line"><h3>{post.author.full_name}</h3>{post.is_announcement && <span className="status-badge">OFFICIAL ANNOUNCEMENT</span>}</div>
              <p style={{ whiteSpace: "pre-wrap" }}>{post.body}</p>
              <small>{new Date(post.created_at).toLocaleString()}</small>
              {(images[post.id] ?? []).length > 0 && <div className="community-image-grid">{images[post.id].map(item => <figure key={item.id}><img src={item.url} alt={"Photo shared by " + post.author.full_name + ": " + item.filename}/><figcaption>{item.filename}</figcaption></figure>)}</div>}
              {isMember && <><label className="button button-quiet button-small community-photo-upload">Attach a photo<input type="file" accept="image/jpeg,image/png,.jpg,.jpeg,.png" disabled={busy} onChange={event => { const file = event.target.files?.[0]; if (file) void uploadImage(post.id, file); event.target.value = ""; }}/></label><label className="button button-quiet button-small community-photo-upload">Attach a video<input type="file" accept="video/mp4,video/webm,video/quicktime,.mp4,.m4v,.webm,.mov" disabled={busy} onChange={event => { const file = event.target.files?.[0]; if (file) void uploadVideo(post.id, file); event.target.value = ""; }}/></label></>}
              {(attachments[post.id] ?? []).length > 0 && <div className="community-video-grid">{attachments[post.id].map(item => <figure key={item.id}><video controls preload="metadata" src={item.url}/><figcaption>{item.filename}</figcaption></figure>)}</div>}
              {isMember && post.author_user_id === user?.id && (post.converted_report_id ? <p className="muted">Official report created: <Link to={"/reports/" + post.converted_report_id}>View report #{post.converted_report_id}</Link></p> : <><button type="button" className="button button-quiet button-small" onClick={() => { setConversionPostId(conversionPostId === post.id ? null : post.id); setConversionTitle(post.body.split("\n")[0].slice(0,180)); setConversionAddress(""); }}>Turn into official report</button>{conversionPostId === post.id && <form className="community-convert-form" onSubmit={event => void convertPost(event, post.id)}><label>Report title<input maxLength={180} value={conversionTitle} onChange={event => setConversionTitle(event.target.value)}/></label><label>Report category<select value={conversionCategory} onChange={event => setConversionCategory(event.target.value)}>{["Infrastructure","Roads and Transport","Water and Sanitation","Electricity","Public Safety","Healthcare","Environment","Other"].map(item => <option key={item}>{item}</option>)}</select></label><label>Street, landmark or nearby building<input required minLength={3} maxLength={300} value={conversionAddress} onChange={event => setConversionAddress(event.target.value)} placeholder="e.g. beside the community health centre"/></label><p className="muted">The selected community supplies the State, LGA and Ward. No GPS coordinates will be requested.</p><div className="form-actions"><button type="button" className="button button-quiet" onClick={() => setConversionPostId(null)}>Cancel</button><button className="button button-primary" disabled={busy || !conversionAddress.trim()}>{busy ? "Submitting…" : "Submit official report"}</button></div></form>}</>)}
              <div className="form-actions"><button className="button button-quiet button-small" type="button" disabled={!isMember} onClick={() => void toggleComments(post.id)}>{expandedPost === post.id ? "Hide comments" : "Comments (" + post.comment_count + ")"}</button></div>
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
