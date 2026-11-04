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

      <section className="home-hero civic-hero">
        <div className="home-hero-copy">
          <p className="eyebrow"><span className="live-dot" /> THE PEOPLE. THE POWER. THE PROGRESS.</p>
          <h1>Our country.<br /><span>Our communities.</span><br />Our voice.</h1>
          <p className="home-hero-description">Change begins when people speak up. Report the issues around you, follow the response, and help build a Nigeria where public institutions listen and act.</p>
          <div className="home-hero-actions">
            <Link className="button button-primary home-primary-cta" to={user ? (user.role === "system_admin" ? "/admin" : "/dashboard") : "/register"}>{user ? "Open your dashboard" : "Raise your voice"} <span aria-hidden="true">→</span></Link>
            <a className="home-secondary-cta" href="#how-it-works">Discover how it works <span aria-hidden="true">↓</span></a>
          </div>
          <div className="home-trust-note"><span className="trust-check">✓</span> Every voice matters. Every report deserves to be heard.</div>
        </div>
        <div className="movement-art" role="img" aria-label="Two raised fists representing people power and civic participation">
          <div className="movement-brush brush-a" /><div className="movement-brush brush-b" />
          <div className="movement-copy"><span>PEOPLE</span><strong>POWER</strong><span>IN ACTION</span></div>
          <div className="movement-fist fist-one" aria-hidden="true">✊</div>
          <div className="movement-fist fist-two" aria-hidden="true">✊</div>
          <div className="movement-caption"><span className="movement-dot" /> YOUR VOICE CAN MOVE THINGS</div>
        </div>
      </section>

      <section className="home-highlights" id="how-it-works">
        <div className="home-section-heading"><p className="eyebrow">A BETTER WAY TO BE HEARD</p><h2>A louder voice. <span>A stronger Nigeria.</span></h2><p>From the first report to the latest update, stay connected to the issues that shape everyday life.</p></div>
        <div className="home-feature-grid">
          {highlights.map((item, index) => <article className="home-feature" key={item.title}><div className={`feature-icon feature-icon-${index + 1}`}>{item.icon}</div><h3>{item.title}</h3><p>{item.text}</p></article>)}
        </div>
      </section>

      <section className="home-bottom-cta"><div><p className="eyebrow">LET'S MAKE THINGS BETTER</p><h2>The future is not a spectator sport.</h2><p>Speak up about what matters. Follow the action. Hold progress in view.</p></div><Link className="button button-light-cta" to={user ? "/dashboard" : "/register"}>{user ? "View your reports" : "Create your free account"} <span aria-hidden="true">→</span></Link></section>
      <footer className="home-footer"><Link className="brand" to="/"><span className="brand-mark">G</span><span>GovConnect<span className="brand-light"> Nigeria</span></span></Link><span>Connecting citizens and public institutions.</span><span>© {new Date().getFullYear()} GovConnect Nigeria</span></footer>
    </main>
  );
}
