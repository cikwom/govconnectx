import { useEffect, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../services/api";
import { useAuth } from "../state/AuthContext";
import type { CommunityPostComment, PublicCommunityPostDetail } from "../types/api";

export default function CommunityPostDetailPage() {
  const { postId } = useParams();
  const { user, loading: authLoading } = useAuth();
  const [post, setPost] = useState<PublicCommunityPostDetail | null>(null);
  const [comments, setComments] = useState<CommunityPostComment[]>([]);
  const [body, setBody] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let active = true;
    const id = Number(postId);
    if (!Number.isInteger(id) || id < 1) {
      setError("This community post could not be found.");
      setLoading(false);
      return () => { active = false; };
    }
    Promise.all([api.publicCommunityPost(id), api.publicCommunityPostComments(id)])
      .then(([postData, commentData]) => {
        if (!active) return;
        setPost(postData);
        setComments(commentData);
      })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : "This discussion could not be loaded."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [postId]);

  async function submitComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!post || !body.trim()) return;
    setSubmitting(true);
    setError("");
    setNotice("");
    try {
      const created = await api.addPublicCommunityPostComment(post.id, body.trim());
      setComments(current => [...current, created]);
      setPost(current => current ? { ...current, comment_count: current.comment_count + 1 } : current);
      setBody("");
      setNotice("Your comment has been published.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Your comment could not be published.");
    } finally {
      setSubmitting(false);
    }
  }

  return <main className="page-stack x-post-detail">
    <Link className="x-post-back" to="/community-connect">← Back to Community Connect</Link>
    {loading || authLoading ? <p role="status">Loading discussion…</p> : error && !post ? <p className="form-error" role="alert">{error}</p> : post && <>
      <article className="x-post-detail-card">
        <p className="eyebrow">{post.is_announcement ? "OFFICIAL ANNOUNCEMENT" : "PUBLIC COMMUNITY POST"}</p>
        <h1>{post.author.full_name}</h1>
        <p className="x-post-location">{post.lga_name}, {post.state_name} · {new Date(post.created_at).toLocaleString()}</p>
        <p className="x-post-detail-body">{post.body}</p>
      </article>
      <section className="x-comments-card" aria-labelledby="comments-heading">
        <h2 id="comments-heading">Comments ({comments.length})</h2>
        {comments.length ? <div className="x-comments-list">{comments.map(comment => <article className="x-comment-item" key={comment.id}>
          <div className="x-comment-meta"><strong>{comment.author.full_name}</strong><span>{new Date(comment.created_at).toLocaleString()}</span></div>
          <p>{comment.body}</p>
        </article>)}</div> : <p className="muted">No comments yet. Start a helpful conversation.</p>}
        {user ? <form className="x-comment-form" onSubmit={submitComment}>
          <label htmlFor="community-comment">Add your comment</label>
          <textarea id="community-comment" value={body} maxLength={2000} onChange={event => setBody(event.target.value)} placeholder="Share a useful, respectful response…" required />
          <button className="button button-primary" type="submit" disabled={submitting || !body.trim()}>{submitting ? "Publishing…" : "Post comment"}</button>
        </form> : <p className="x-comment-signin">You can read all comments without an account. <Link to="/login">Sign in</Link> to join the discussion.</p>}
        {error && <p className="form-error" role="alert">{error}</p>}
        {notice && <p className="form-success" role="status">{notice}</p>}
      </section>
    </>}
  </main>;
}
