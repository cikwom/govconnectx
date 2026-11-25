import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent, ChangeEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { api, tokenStore } from "../services/api";
import type { CommunityChatMessage } from "../types/api";
import { useAuth } from "../state/AuthContext";

export default function CommunityChatPage() {
  const { communityCode = "" } = useParams();
  const { user } = useAuth();
  const [messages, setMessages] = useState<CommunityChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [isMember, setIsMember] = useState(false);
  const [sending, setSending] = useState(false);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState("");
  // undefined = not loaded, null = failed, string = object URL.
  const [photoUrls, setPhotoUrls] = useState<Record<number, string | null>>({});
  const photoUrlsRef = useRef<string[]>([]);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const cameraInputRef = useRef<HTMLInputElement | null>(null);
  const galleryInputRef = useRef<HTMLInputElement | null>(null);

  const refresh = useCallback(async () => {
    const result = await api.communityChatMessages(communityCode);
    setMessages(result);
    return result;
  }, [communityCode]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    api.communityMembership(communityCode).then(async membership => {
      if (!active) return;
      setIsMember(membership.is_member);
      if (!membership.is_member) { setError("Join this community from Community Connect before opening its group chat."); return; }
      await refresh();
    }).catch(reason => { if (active) setError(reason instanceof Error ? reason.message : "Could not verify community membership."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [refresh]);

  useEffect(() => {
    if (!communityCode || !isMember) return;
    let disposed = false;
    let retryTimer: number | undefined;
    const socket = api.openCommunitySocket(communityCode);
    socket.onopen = () => { const token = tokenStore.get(); if (!token) { socket.close(); return; } socket.send(JSON.stringify({ type: "authenticate", token })); };
    socket.onmessage = event => {
      try {
        const incoming = JSON.parse(String(event.data)) as { type?: string };
        if (incoming.type === "connected") { setConnected(true); return; }
        if (incoming.type === "pong") return;
        if (incoming.type === "chat_message_created") api.communityChatMessages(communityCode).then(setMessages).catch(() => undefined);
      } catch { /* Ignore malformed live events. */ }
    };
    socket.onclose = () => { if (!disposed) { setConnected(false); retryTimer = window.setTimeout(() => setRetry(value => value + 1), 5000); } };
    socket.onerror = () => { if (!disposed) setConnected(false); };
    const heartbeat = window.setInterval(() => { if (socket.readyState === WebSocket.OPEN) socket.send("ping"); }, 25000);
    return () => { disposed = true; window.clearInterval(heartbeat); if (retryTimer !== undefined) window.clearTimeout(retryTimer); socket.close(); };
  }, [communityCode, isMember, retry]);

  useEffect(() => {
    if (!communityCode || !isMember || connected) return;
    const timer = window.setInterval(() => { api.communityChatMessages(communityCode).then(setMessages).catch(() => undefined); }, 10000);
    return () => window.clearInterval(timer);
  }, [communityCode, isMember, connected]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [messages.length]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const targets = messages.filter(message => message.image_id && photoUrls[message.id] === undefined);
      if (!targets.length) return;
      const loaded = await Promise.all(targets.map(async message => {
        try {
          const url = URL.createObjectURL(await api.downloadCommunityChatPhoto(communityCode, message.id));
          photoUrlsRef.current.push(url);
          return [message.id, url] as const;
        } catch {
          return [message.id, null] as const;
        }
      }));
      if (cancelled) {
        loaded.forEach(([, url]) => { if (url) { URL.revokeObjectURL(url); photoUrlsRef.current = photoUrlsRef.current.filter(item => item !== url); } });
        return;
      }
      setPhotoUrls(current => {
        const next = { ...current };
        loaded.forEach(([id, url]) => { next[id] = url; });
        return next;
      });
    };
    void load();
    return () => { cancelled = true; };
  }, [communityCode, messages, photoUrls]);

  useEffect(() => () => photoUrlsRef.current.forEach(URL.revokeObjectURL), []);

  // Revoke the previous preview when another photo is selected, removed, or the page unmounts.
  useEffect(() => {
    if (!photoPreview) return;
    return () => URL.revokeObjectURL(photoPreview);
  }, [photoPreview]);

  function selectPhoto(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
    if (!selected) return;
    if (!["image/jpeg", "image/png"].includes(selected.type)) { setError("Choose a JPEG or PNG photo."); event.target.value = ""; return; }
    if (selected.size > 10 * 1024 * 1024) { setError("Photos must be 10 MB or smaller."); event.target.value = ""; return; }
    setError("");
    setPhoto(selected);
    setPhotoPreview(URL.createObjectURL(selected));
    event.target.value = "";
  }

  function clearPhoto() {
    setPhoto(null);
    setPhotoPreview("");
  }

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    const body = draft.trim();
    if ((!body && !photo) || sending) return;
    setSending(true); setError("");
    try {
      const created = photo ? await api.uploadCommunityChatPhoto(communityCode, photo, body) : await api.sendCommunityChatMessage(communityCode, body);
      setMessages(current => current.some(item => item.id === created.id) ? current : [...current, created]);
      setDraft(""); clearPhoto();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Message could not be sent."); }
    finally { setSending(false); }
  }

  return <div className="page-stack community-chat-page">
    <section className="citizen-dashboard-banner"><div><p className="eyebrow">COMMUNITY CONNECT · GROUP CHAT</p><h1>Your community, in conversation.</h1><p>Share useful updates and photos with verified members of this community.</p></div><span className="dashboard-fist" aria-hidden="true">◎</span></section>
    <section className="panel community-chat-panel">
      <div className="panel-heading"><div><p className="eyebrow">COMMUNITY ROOM</p><h2>{communityCode}</h2><p className="muted">Messages and photos are visible to active members only.</p></div><span className={connected ? "chat-connection online" : "chat-connection"}>{connected ? "Live" : "Reconnecting"}</span></div>
      <div className="community-chat-toolbar"><Link to="/community-connect">← Back to Community Connect</Link><span>{messages.length} recent messages</span></div>
      <div className="community-chat-messages" aria-live="polite" aria-label="Community chat messages">
        {loading ? <p className="muted">Loading conversation…</p> : messages.length === 0 ? <div className="chat-empty"><strong>Start the conversation</strong><p>There are no messages yet. Share a helpful update or photo with your neighbours.</p></div> : messages.map(message => (
          <article className={message.author_user_id === user?.id ? "chat-message own" : "chat-message"} key={message.id}>
            <div className="chat-message-meta"><strong>{message.author.full_name}</strong><time dateTime={message.created_at}>{new Date(message.created_at).toLocaleString()}</time></div>
            {message.body && <p>{message.body}</p>}
            {message.image_id && (photoUrls[message.id] ? <img className="chat-message-photo" src={photoUrls[message.id] as string} alt={message.image_original_filename || "Photo shared in community chat"}/> : photoUrls[message.id] === null ? <p className="muted" role="status">This photo could not be loaded. Refresh the conversation to try again.</p> : <p className="muted">Loading photo…</p>)}
          </article>
        ))}
        <div ref={bottomRef}/>
      </div>
      {error && <p className="form-error" role="alert">{error}</p>}
      {isMember && <>
        {photoPreview && <div className="chat-photo-preview"><img src={photoPreview} alt="Selected photo preview"/><button className="button button-quiet button-small" type="button" onClick={clearPhoto}>Remove photo</button></div>}
        <form className="community-chat-compose" onSubmit={sendMessage}>
          <label className="sr-only" htmlFor="community-chat-message">Write a message or photo caption</label>
          <textarea id="community-chat-message" value={draft} onChange={event => setDraft(event.target.value)} maxLength={2000} rows={2} placeholder="Write a message or photo caption…"/>
          <div className="chat-compose-actions">
            <input ref={cameraInputRef} className="sr-only" type="file" accept="image/jpeg,image/png" capture="environment" onChange={selectPhoto}/>
            <input ref={galleryInputRef} className="sr-only" type="file" accept="image/jpeg,image/png" onChange={selectPhoto}/>
            <button className="button button-quiet" type="button" onClick={() => cameraInputRef.current?.click()}>Take photo</button>
            <button className="button button-quiet" type="button" onClick={() => galleryInputRef.current?.click()}>Choose photo</button>
            <button className="button button-primary" type="submit" disabled={sending || (!draft.trim() && !photo)}>{sending ? "Sending…" : photo ? "Share photo" : "Send message"}</button>
          </div>
        </form>
        <p className="muted chat-guidance">JPEG and PNG photos up to 10 MB. Photos are scanned and stored privately. Do not share passwords or private personal details.</p>
      </>}
    </section>
  </div>;
}
