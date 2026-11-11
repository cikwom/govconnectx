import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../state/AuthContext";
import ThemeToggle from "./ThemeToggle";
import LanguageSelector from "./LanguageSelector";
import { useEffect } from "react";
import { api } from "../services/api";
import { useLanguage } from "../state/LanguageContext";

export default function AppShell() {
  const { user, signOut } = useAuth();
  const { setLanguage, t } = useLanguage();
  useEffect(() => { if (user) api.preferences().then(value => setLanguage(value.preferred_language)).catch(() => undefined); }, [user, setLanguage]);
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">{t("Skip to main content")}</a>
      <header className="topbar">
        <NavLink className="brand" to="/"><span className="brand-mark">G</span><span>GovConnect<span className="brand-light"> Nigeria</span></span></NavLink>
        <div className="topbar-user">
          <NavLink className="admin-nav-link" to="/community-services">{t("Community services")}</NavLink>
          {user?.role === "system_admin" && <NavLink className="admin-nav-link" to="/admin">{t("Command Centre")}</NavLink>}
          <NavLink className="admin-nav-link" to="/preferences">{t("Preferences")}</NavLink>
          <LanguageSelector />
          <ThemeToggle />
          <div className="user-copy"><strong>{user?.full_name}</strong><span>{user?.role.replaceAll("_", " ")}</span></div>
          <button className="button button-quiet button-small" onClick={signOut}>{t("Sign out")}</button>
        </div>
      </header>
      <main id="main-content" className="page-content" tabIndex={-1}><Outlet /></main>
      <footer className="footer legal-app-footer">
        <span>{t("GovConnect Nigeria · Making public services more accountable")}</span>
        <nav aria-label="Legal links"><NavLink to="/terms">Terms of Use</NavLink><NavLink to="/privacy">Privacy Notice</NavLink></nav>
      </footer>
    </div>
  );
}
