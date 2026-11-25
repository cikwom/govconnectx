import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
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
  const bottomRef = useRef<HTMLDivElement | null>(null);

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
      if (!membership.is_member) {
        setError("Join this community from Community Connect before opening its group chat.");
        return;
      }
      await refresh();
    }).catch(reason => {
      if (active) setError(reason instanceof Error ? reason.message : "Could not verify community membership.");
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [refresh]);

  useEffect(() => {
    if (!communityCode || !isMember) return;
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
        const incoming = JSON.parse(String(event.data)) as { type?: string };
        if (incoming.type === "connected") { setConnected(true); return; }
        if (incoming.type === "pong") return;
        if (incoming.type === "chat_message_created") {
          api.communityChatMessages(communityCode).then(setMessages).catch(() => undefined);
        }
      } catch { /* Ignore malformed live events. */ }
    };
    socket.onclose = () => {
      if (!disposed) {
        setConnected(false);
        retryTimer = window.setTimeout(() => setRetry(value => value + 1), 5000);
      }
    };
    socket.onerror = () => { if (!disposed) setConnected(false); };
    const heartbeat = window.setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) socket.send("ping");
    }, 25000);
    return () => {
      disposed = true;
      window.clearInterval(heartbeat);
      if (retryTimer !== undefined) window.clearTimeout(retryTimer);
      socket.close();
    };
  }, [communityCode, isMember, retry]);

  useEffect(() => {
    if (!communityCode || !isMember || connected) return;
    const timer = window.setInterval(() => {
      api.communityChatMessages(communityCode).then(setMessages).catch(() => undefined);
    }, 10000);
    return () => window.clearInterval(timer);
  }, [communityCode, isMember, connected]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [messages.length]);

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    const body = draft.trim();
    if (!body || sending) return;
    setSending(true);
    setError("");
    try {
      const created = await api.sendCommunityChatMessage(communityCode, body);
      setMessages(current => current.some(item => item.id === created.id) ? current : [...current, created]);
      setDraft("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Message could not be sent.");
    } finally { setSending(false); }
  }

  return <div className="page-stack community-chat-page">
    <section className="citizen-dashboard-banner">
      <div><p className="eyebrow">COMMUNITY CONNECT · GROUP CHAT</p><h1>Your community, in conversation.</h1><p>Share useful updates with verified members of this community. Keep messages respectful and relevant.</p></div>
      <span className="dashboard-fist" aria-hidden="true">◎</span>
    </section>
    <section className="panel community-chat-panel">
      <div className="panel-heading">
        <div><p className="eyebrow">COMMUNITY ROOM</p><h2>{communityCode}</h2><p className="muted">Messages are visible to active members of this community only.</p></div>
        <span className={connected ? "chat-connection online" : "chat-connection"}>{connected ? "Live" : "Reconnecting"}</span>
      </div>
      <div className="community-chat-toolbar"><Link to="/community-connect">← Back to Community Connect</Link><span>{messages.length} recent messages</span></div>
      <div className="community-chat-messages" aria-live="polite" aria-label="Community chat messages">
        {loading ? <p className="muted">Loading conversation…</p> : messages.length === 0 ? <div className="chat-empty"><strong>Start the conversation</strong><p>There are no messages yet. Share a helpful update with your neighbours.</p></div> : messages.map(message => (
          <article className={message.author_user_id === user?.id ? "chat-message own" : "chat-message"} key={message.id}>
            <div className="chat-message-meta"><strong>{message.author.full_name}</strong><time dateTime={message.created_at}>{new Date(message.created_at).toLocaleString()}</time></div>
            <p>{message.body}</p>
          </article>
        ))}
        <div ref={bottomRef}/>
      </div>
      {error && <p className="form-error" role="alert">{error}</p>}
      {isMember && <><form className="community-chat-compose" onSubmit={sendMessage}>
        <label className="sr-only" htmlFor="community-chat-message">Write a message</label>
        <textarea id="community-chat-message" value={draft} onChange={event => setDraft(event.target.value)} maxLength={2000} rows={2} placeholder="Write a message to your community…" required/>
        <button className="button button-primary" type="submit" disabled={sending || !draft.trim()}>{sending ? "Sending…" : "Send message"}</button>
      </form>
      <p className="muted chat-guidance">Please do not share passwords, private personal details or unverified accusations.</p></>}
    </section>
  </div>;
}
