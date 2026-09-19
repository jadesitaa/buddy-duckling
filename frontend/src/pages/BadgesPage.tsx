import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { Habit, UserBadge } from "../api/types";

export function BadgesPage() {
  const [badges, setBadges] = useState<UserBadge[] | null>(null);
  const [habits, setHabits] = useState<Habit[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.badges(), api.habits()])
      .then(([earned, myHabits]) => {
        setBadges(earned);
        setHabits(myHabits);
      })
      .catch((caught: unknown) =>
        setError(caught instanceof Error ? caught.message : "Could not load"),
      );
  }, []);

  if (!badges) return <p className="muted">{error ?? "Loading…"}</p>;

  const habitName = (id: number) =>
    habits.find((habit) => habit.id === id)?.name ?? "a habit";

  return (
    <div className="stack">
      <h2 style={{ margin: 0 }}>Badges</h2>

      {badges.length === 0 ? (
        <p className="card muted">
          No badges yet. The first one arrives after a 3 day streak.
        </p>
      ) : (
        <ul
          style={{
            listStyle: "none",
            padding: 0,
            margin: 0,
            display: "grid",
            gap: "1rem",
            gridTemplateColumns: "repeat(auto-fill, minmax(210px, 1fr))",
          }}
        >
          {badges.map((earned) => (
            <li key={earned.id} className="card" style={{ textAlign: "center" }}>
              <div style={{ fontSize: "2.2rem" }}>🏅</div>
              <strong>{earned.badge.title}</strong>
              <p className="muted" style={{ margin: "0.2rem 0 0" }}>
                {earned.badge.milestone_days} day streak
                <br />
                on {habitName(earned.habit_id)}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
