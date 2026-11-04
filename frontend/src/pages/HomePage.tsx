import { Link } from "react-router-dom";
import ThemeToggle from "../components/ThemeToggle";
import { useAuth } from "../state/AuthContext";

const highlights = [
  { icon: "◎", title: "Report local issues", text: "Share what is happening in your neighbourhood and where it needs attention." },
  { icon: "↗", title: "Follow every update", text: "See when a report is received, reviewed, assigned and resolved." },
  { icon: "✳", title: "Build better communities", text: "Help public institutions understand what matters to the people they serve." },
];

export default function HomePage() {
  const { user } = useAuth();
  return (
    <main className="home-page">
      <header className="home-nav">
        <Link className="brand" to="/"><span className="brand-mark">G</span><span>GovConnect<span className="brand-light"> Nigeria</span></span></Link>
        <nav className="home-nav-actions" aria-label="Main navigation">
          <a href="#how-it-works">How it works</a>
          <ThemeToggle />
          {user
            ? <Link className="button button-primary" to={user.role === "system_admin" ? "/admin" : "/dashboard"}>Open dashboard</Link>
            : <><Link className="home-login-link" to="/login">Sign in</Link><Link className="button button-primary" to="/register">Get started <span aria-hidden="true">→</span></Link></>}
        </nav>
      </header>

      <section className="home-hero">
        <div className="home-hero-copy">
          <p className="eyebrow"><span className="live-dot" /> CITIZEN VOICE · PUBLIC ACTION</p>
          <h1>Your community.<br /><span>Your voice.</span> Real progress.</h1>
          <p className="home-hero-description">A simple way to report community issues, follow what happens next, and help make public services work better for everyone.</p>
          <div className="home-hero-actions">
            <Link className="button button-primary home-primary-cta" to={user ? (user.role === "system_admin" ? "/admin" : "/dashboard") : "/register"}>{user ? "Go to your dashboard" : "Make your voice heard"} <span aria-hidden="true">→</span></Link>
            <a className="home-secondary-cta" href="#how-it-works">See how it works <span aria-hidden="true">↓</span></a>
          </div>
          <div className="home-trust-note"><span className="trust-check">✓</span> Your report. Clear updates. A more accountable community.</div>
        </div>
        <div className="home-hero-art" aria-label="Illustration of a community connected through public services">
          <div className="hero-orbit orbit-one" /><div className="hero-orbit orbit-two" />
          <div className="hero-sun" />
          <div className="hero-building building-back"><span /><span /><span /></div>
          <div className="hero-building building-front"><span /><span /><span /><span /></div>
          <div className="hero-pin"><span>✓</span></div>
          <div className="hero-note note-top"><span className="note-icon">✳</span><span><strong>Community voice</strong><small>Seen and heard</small></span></div>
          <div className="hero-note note-bottom"><span className="note-icon note-icon-green">↗</span><span><strong>Progress you can follow</strong><small>Every step, in one place</small></span></div>
          <div className="hero-ground" />
        </div>
      </section>

      <section className="home-highlights" id="how-it-works">
        <div className="home-section-heading"><p className="eyebrow">A BETTER WAY TO BE HEARD</p><h2>Small actions can make a <span>big difference.</span></h2><p>From the first report to the latest update, stay connected to the issues that shape everyday life.</p></div>
        <div className="home-feature-grid">
          {highlights.map((item, index) => <article className="home-feature" key={item.title}><div className={`feature-icon feature-icon-${index + 1}`}>{item.icon}</div><h3>{item.title}</h3><p>{item.text}</p></article>)}
        </div>
      </section>

      <section className="home-bottom-cta"><div><p className="eyebrow">LET'S MAKE THINGS BETTER</p><h2>Be part of the change.</h2><p>Join the conversation and help move your community forward.</p></div><Link className="button button-light-cta" to={user ? "/dashboard" : "/register"}>{user ? "View your reports" : "Create your free account"} <span aria-hidden="true">→</span></Link></section>
      <footer className="home-footer"><Link className="brand" to="/"><span className="brand-mark">G</span><span>GovConnect<span className="brand-light"> Nigeria</span></span></Link><span>Connecting citizens and public institutions.</span><span>© {new Date().getFullYear()} GovConnect Nigeria</span></footer>
    </main>
  );
}
