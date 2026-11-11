import { Link } from "react-router-dom";
import ThemeToggle from "../components/ThemeToggle";
import LanguageSelector from "../components/LanguageSelector";
import { useLanguage } from "../state/LanguageContext";
import { useAuth } from "../state/AuthContext";

const highlights = [
  { number: "01", icon: "◎", title: "Speak up where you live", text: "Report broken infrastructure, safety concerns and public-service issues in your community." },
  { number: "02", icon: "↗", title: "See what happens next", text: "Follow your report as it is received, reviewed, assigned and resolved." },
  { number: "03", icon: "✳", title: "Move Nigeria forward", text: "Turn everyday experiences into clear signals that institutions can act on." },
];

function NigeriaLandscape() {
  return (
    <svg className="nigeria-landscape" viewBox="0 0 900 650" role="img" aria-label="Watercolour illustration of the Nigerian flag above a peaceful green landscape">
      <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#f8f1d9"/><stop offset=".52" stopColor="#d9e9d8"/><stop offset="1" stopColor="#a8cdbb"/></linearGradient>
        <linearGradient id="water" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#5d9d83"/><stop offset="1" stopColor="#174f3d"/></linearGradient>
        <linearGradient id="hill" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#4b9876"/><stop offset="1" stopColor="#174d39"/></linearGradient>
        <linearGradient id="flagGreen" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#087b4c"/><stop offset="1" stopColor="#003f2c"/></linearGradient>
        <filter id="wash"><feTurbulence type="fractalNoise" baseFrequency=".018" numOctaves="3" seed="8"/><feDisplacementMap in="SourceGraphic" scale="13"/></filter>
        <filter id="soft"><feGaussianBlur stdDeviation="18"/></filter>
        <clipPath id="flagShape"><path d="M158 102 Q260 142 375 119 Q470 101 555 143 L552 318 Q449 284 359 310 Q258 337 160 285Z"/></clipPath>
      </defs>
      <rect width="900" height="650" fill="url(#sky)"/>
      <g opacity=".45" filter="url(#soft)"><ellipse cx="180" cy="140" rx="210" ry="95" fill="#fff9dc"/><ellipse cx="690" cy="160" rx="220" ry="120" fill="#c1dfd0"/><ellipse cx="465" cy="45" rx="180" ry="70" fill="#fff8df"/></g>
      <g fill="#e9f0d9" opacity=".45" filter="url(#wash)"><path d="M0 245Q120 145 260 230T530 205T900 215V390H0Z"/><path d="M0 330Q190 250 360 325T700 295T900 330V430H0Z"/></g>
      <path d="M0 395Q110 330 235 382T470 365T700 370T900 340V650H0Z" fill="#6da88a" opacity=".7"/>
      <path d="M0 425Q135 355 255 410T500 392T720 395T900 370V650H0Z" fill="url(#hill)"/>
      <g fill="#174f3b" opacity=".9">
        <path d="M0 434l34-94 28 94zM42 436l42-122 38 122zM95 431l28-82 30 82zM160 438l44-133 40 133zM220 435l32-99 30 99zM620 410l40-122 38 122zM680 408l30-95 33 95zM740 405l44-135 42 135zM810 403l34-105 31 105zM865 404l27-83 28 83z"/>
      </g>
      <g fill="#2b7654" opacity=".85"><path d="M0 460q170-65 320 5t300-4t280-12v95H0z"/><path d="M0 490q180-45 350 12t300-7t250-10v70H0z"/></g>
      <path d="M0 470Q170 438 320 470T620 462T900 450V650H0Z" fill="url(#water)" opacity=".9"/>
      <g stroke="#d2e6ce" strokeWidth="3" opacity=".3" fill="none"><path d="M0 500q150-18 300 0t300 0t300 0"/><path d="M80 535q130-13 260 0t260 0t260 0"/><path d="M0 575q160-14 320 0t320 0t260 0"/></g>
      <g stroke="#164d38" strokeWidth="5" opacity=".8"><path d="M0 650q15-65 6-105m25 105q-3-49 12-80m32 80q-5-62 12-100m40 100q-2-45 16-75m45 75q-7-57 8-91m640 91q-5-55 13-91m31 91q-2-45 16-75m24 75q-4-57 10-95"/></g>
      <g opacity=".35" fill="#f8f3d9"><circle cx="90" cy="382" r="4"/><circle cx="120" cy="420" r="3"/><circle cx="275" cy="360" r="4"/><circle cx="710" cy="350" r="3"/><circle cx="820" cy="390" r="4"/><circle cx="565" cy="435" r="3"/><circle cx="430" cy="345" r="3"/></g>
      <path d="M155 80L151 492" stroke="#324f3e" strokeWidth="8" strokeLinecap="round"/>
      <path d="M158 102 Q260 142 375 119 Q470 101 555 143 L552 318 Q449 284 359 310 Q258 337 160 285Z" fill="#f8f4df" opacity=".92"/>
      <g clipPath="url(#flagShape)">
        <path d="M130 70H290V350H130Z" fill="url(#flagGreen)"/>
        <path d="M290 70H450V350H290Z" fill="#f8f5df"/>
        <path d="M450 70H590V350H450Z" fill="url(#flagGreen)"/>
        <path d="M150 100Q265 145 380 120T570 145" fill="none" stroke="#ffffff" strokeWidth="14" opacity=".13"/>
        <path d="M150 280Q280 325 390 295T560 300" fill="none" stroke="#003d2b" strokeWidth="17" opacity=".2"/>
      </g>
      <g fill="#fff8df" opacity=".55"><circle cx="620" cy="250" r="3"/><circle cx="674" cy="310" r="4"/><circle cx="740" cy="235" r="3"/><circle cx="805" cy="300" r="3"/><circle cx="590" cy="365" r="3"/><circle cx="370" cy="390" r="3"/><circle cx="220" cy="360" r="3"/><circle cx="775" cy="430" r="4"/></g>
      <g fill="#d8e9d2" opacity=".18"><path d="M0 0h900v650H0z" filter="url(#wash)"/></g>
    </svg>
  );
}

export default function HomePage() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const destination = user ? (user.role === "system_admin" ? "/admin" : "/dashboard") : "/register";

  return (
    <main className="home-page">
      <header className="home-nav">
        <Link className="brand" to="/"><span className="brand-mark">G</span><span>GovConnect<span className="brand-light"> Nigeria</span></span></Link>
        <nav className="home-nav-actions" aria-label={t("Main navigation")}>
          <a href="#how-it-works">{t("How it works")}</a>
          <a href="#our-purpose">{t("Our purpose")}</a>
          <Link to="/transparency">{t("Transparency")}</Link>
          <LanguageSelector />
          <ThemeToggle />
          {user
            ? <Link className="button button-primary" to={destination}>{t("Open dashboard")} <span aria-hidden="true">→</span></Link>
            : <><Link className="home-login-link" to="/login">{t("Sign in")}</Link><Link className="home-login-link" to="/admin/login">{t("Government / Admin")}</Link><Link className="button button-primary" to="/register">{t("Get started")} <span aria-hidden="true">→</span></Link></>}
        </nav>
      </header>

      <section className="home-hero civic-hero">
        <div className="home-hero-copy">
          <p className="eyebrow"><span className="live-dot" /> {t("A NATION THAT LISTENS, A PEOPLE THAT LEAD")}</p>
          <h1>{t("Nigeria is")} <em>{t("ours.")}</em><br />{t("Let’s make it")}<br /><span>{t("better together.")}</span></h1>
          <p className="home-hero-description">{t("Your community deserves to be heard. Report the issues that matter, follow real progress, and help build a country where every voice can make a difference.")}</p>
          <div className="home-hero-actions">
            <Link className="button button-primary home-primary-cta" to={destination}>{user ? t("Open your dashboard") : t("Make your voice heard")} <span aria-hidden="true">→</span></Link>
            <a className="home-secondary-cta" href="#how-it-works">{t("See how it works")} <span aria-hidden="true">↓</span></a>
          </div>
          <div className="home-trust-note"><span className="trust-check">✓</span> {t("Your voice matters. Your community matters.")}</div>
        </div>
        <div className="landscape-frame">
          <NigeriaLandscape />
          <div className="landscape-label"><span className="landscape-label-mark">✳</span><span><strong>One Nigeria. Many voices.</strong><small>Progress begins in our communities.</small></span></div>
          <div className="landscape-stamp">OUR HOME<br /><b>OUR FUTURE</b></div>
        </div>
      </section>

      <section className="home-purpose" id="our-purpose">
        <div className="purpose-kicker"><span>01</span><p className="eyebrow">CITIZENS AND INSTITUTIONS, CONNECTED</p></div>
        <div className="purpose-content"><h2>{t("A better Nigeria starts with")} <span>{t("being heard.")}</span></h2><p>{t("GovConnect gives people a clear way to raise local concerns and gives public institutions a better view of what communities need. No noise. No guesswork. Just a more direct path from reporting to response.")}</p></div>
        <div className="purpose-side-note">LISTEN<br /><span>→</span><br />RESPOND<br /><span>→</span><br />IMPROVE</div>
      </section>

      <section className="home-highlights" id="how-it-works">
        <div className="home-section-heading"><p className="eyebrow">{t("FROM YOUR STREET TO THE PEOPLE WHO CAN HELP")}</p><h2>{t("Small actions.")} <span>{t("Real progress.")}</span></h2><p>{t("One simple place to report issues, stay informed and see your community move forward.")}</p></div>
        <div className="home-feature-grid">
          {highlights.map((item) => <article className="home-feature" key={item.title}><div className="feature-topline"><span>{item.number}</span><span className="feature-icon">{item.icon}</span></div><h3>{t(item.title)}</h3><p>{t(item.text)}</p></article>)}
        </div>
      </section>

      <section className="home-bottom-cta"><div><p className="eyebrow">{t("THE NEXT CHAPTER STARTS WITH US")}</p><h2>{t("Let’s build the Nigeria we want to live in.")}</h2><p>{t("Raise a concern. Follow the response. Be part of the progress.")}</p></div><Link className="button button-light-cta" to={destination}>{user ? t("Go to your dashboard") : t("Join GovConnect")} <span aria-hidden="true">→</span></Link></section>
      <footer className="home-footer"><Link className="brand" to="/"><span className="brand-mark">G</span><span>GovConnect<span className="brand-light"> Nigeria</span></span></Link><span>{t("Connecting citizens and public institutions.")}</span><nav className="home-legal-links" aria-label="Legal links"><Link to="/terms">Terms of Use</Link><Link to="/privacy">Privacy Notice</Link></nav><span>© {new Date().getFullYear()} GovConnect Nigeria</span></footer>
    </main>
  );
}
