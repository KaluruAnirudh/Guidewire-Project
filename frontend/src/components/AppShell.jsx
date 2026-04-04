import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext";


function linkClassName({ isActive }) {
  return isActive ? "nav-link active" : "nav-link";
}


export default function AppShell() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Parametric income protection</p>
          <h1 className="brand">GigInsure AI</h1>
        </div>
        <nav className="nav-links">
          <NavLink className={linkClassName} to="/dashboard">
            Dashboard
          </NavLink>
          <NavLink className={linkClassName} to="/policy">
            Buy Policy
          </NavLink>
          <NavLink className={linkClassName} to="/claims/new">
            Submit Claim
          </NavLink>
          <NavLink className={linkClassName} to="/claims">
            Claim Status
          </NavLink>
          <button className="button ghost" onClick={logout} type="button">
            Sign out
          </button>
        </nav>
      </header>

      <section className="hero-strip">
        <div>
          <p className="hero-kicker">Active worker</p>
          <h2>{user?.name}</h2>
        </div>
        <div className="hero-meta">
          <span>{user?.work_type}</span>
          <span>Weekly est. {user?.weekly_earnings_estimate}</span>
          <span>
            {user?.location?.lat}, {user?.location?.lon}
          </span>
        </div>
      </section>

      <main className="page-content">
        <Outlet />
      </main>
    </div>
  );
}

