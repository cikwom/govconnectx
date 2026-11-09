import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../state/AuthContext";
import ThemeToggle from "./ThemeToggle";

export default function AppShell() {
  const { user, signOut } = useAuth();
  return (
    <div className="app-shell">
      <header className="topbar">
        <NavLink className="brand" to="/"><span className="brand-mark">G</span><span>GovConnect<span className="brand-light"> Nigeria</span></span></NavLink>
        <div className="topbar-user">
          {user?.role === "system_admin" && <NavLink className="admin-nav-link" to="/admin">Command Centre</NavLink>}
          <ThemeToggle />
          <div className="user-copy"><strong>{user?.full_name}</strong><span>{user?.role.replaceAll("_", " ")}</span></div>
          <button className="button button-quiet button-small" onClick={signOut}>Sign out</button>
        </div>
      </header>
      <main className="page-content"><Outlet /></main>
      <footer className="footer legal-app-footer">
        <span>GovConnect Nigeria · Making public services more accountable</span>
        <nav aria-label="Legal links"><NavLink to="/terms">Terms of Use</NavLink><NavLink to="/privacy">Privacy Notice</NavLink></nav>
      </footer>
    </div>
  );
}
