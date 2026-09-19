import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { DuckAvatar } from "./DuckAvatar";

const links = [
  { to: "/", label: "Habits", end: true },
  { to: "/buddies", label: "Buddies" },
  { to: "/notifications", label: "Notifications" },
  { to: "/badges", label: "Badges" },
  { to: "/profile", label: "Profile" },
];

export function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [unread, setUnread] = useState(0);
  const [requests, setRequests] = useState(0);

  // Refresh the counters whenever the page changes, so acting on something
  // anywhere in the app updates the badges in the nav.
  useEffect(() => {
    api
      .dashboard()
      .then((dashboard) => {
        setUnread(dashboard.unread_notifications);
        setRequests(dashboard.pending_partner_requests);
      })
      .catch(() => undefined);
  }, [location.pathname]);

  function badgeFor(label: string): number {
    if (label === "Notifications") return unread;
    if (label === "Buddies") return requests;
    return 0;
  }

  return (
    <div className="page stack">
      <header className="spread">
        <div className="row">
          <DuckAvatar code={user?.avatar ?? "clover"} size={44} />
          <div>
            <strong>Buddy Duckling</strong>
            <p className="muted" style={{ margin: 0 }}>
              {user?.display_name}
            </p>
          </div>
        </div>
        <button className="ghost" onClick={logout}>
          Sign out
        </button>
      </header>

      <nav className="row" style={{ flexWrap: "wrap" }}>
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) => `tab${isActive ? " active" : ""}`}
          >
            {link.label}
            {badgeFor(link.label) > 0 && (
              <span className="dot">{badgeFor(link.label)}</span>
            )}
          </NavLink>
        ))}
      </nav>

      <Outlet />
    </div>
  );
}
