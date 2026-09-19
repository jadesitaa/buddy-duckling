import { useCallback, useEffect, useState } from "react";

import { api } from "../api/client";
import type { AppNotification, NotificationType } from "../api/types";

const icons: Record<NotificationType, string> = {
  streak_broken: "💔",
  partner_request: "🤝",
  partner_accepted: "🎉",
  partner_declined: "🙈",
  waiting_for_partner: "⏳",
  goal_achieved: "🏆",
  badge_earned: "🏅",
};

function whenever(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function NotificationsPage() {
  const [items, setItems] = useState<AppNotification[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setItems(await api.notifications());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function markRead(id: number) {
    await api.markNotificationRead(id);
    await load();
  }

  async function markAllRead() {
    await api.markAllNotificationsRead();
    await load();
  }

  if (!items) return <p className="muted">{error ?? "Loading…"}</p>;

  const unread = items.filter((item) => !item.is_read).length;

  return (
    <div className="stack">
      <div className="spread">
        <h2 style={{ margin: 0 }}>Notifications</h2>
        {unread > 0 && (
          <button className="secondary" onClick={markAllRead}>
            Mark all read ({unread})
          </button>
        )}
      </div>

      {error && <p className="error">{error}</p>}

      {items.length === 0 ? (
        <p className="card muted">Nothing here yet. Quiet is good too.</p>
      ) : (
        <ul className="stack" style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {items.map((item) => (
            <li
              key={item.id}
              className="card spread"
              style={{ opacity: item.is_read ? 0.6 : 1 }}
            >
              <div className="row" style={{ alignItems: "flex-start" }}>
                <span style={{ fontSize: "1.4rem" }}>{icons[item.type]}</span>
                <div>
                  <strong>{item.title}</strong>
                  <p style={{ margin: "0.15rem 0" }}>{item.body}</p>
                  <p className="muted" style={{ margin: 0 }}>
                    {whenever(item.created_at)}
                  </p>
                </div>
              </div>
              {!item.is_read && (
                <button className="ghost" onClick={() => markRead(item.id)}>
                  Mark read
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
