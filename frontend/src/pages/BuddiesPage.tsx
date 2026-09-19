import { useCallback, useEffect, useState } from "react";

import { api } from "../api/client";
import type { Habit, Partnership } from "../api/types";
import { DuckAvatar } from "../components/DuckAvatar";
import { GoalList } from "../components/GoalList";

const STATUS: Record<Partnership["status"], { label: string; tone: string }> = {
  pending: { label: "⏳ Waiting for their answer", tone: "warn" },
  accepted: { label: "✅ Buddies", tone: "good" },
  declined: { label: "🙈 They said no", tone: "off" },
};

const EMPTY_INVITE = { habitId: "" as number | "", email: "" };

export function BuddiesPage() {
  const [habits, setHabits] = useState<Habit[]>([]);
  const [sent, setSent] = useState<Partnership[]>([]);
  const [requests, setRequests] = useState<Partnership[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // The invite form stays folded away until it is asked for.
  const [inviting, setInviting] = useState(false);
  const [invite, setInvite] = useState(EMPTY_INVITE);
  const [pairWith, setPairWith] = useState<Record<number, number | "">>({});

  const load = useCallback(async () => {
    try {
      const myHabits = await api.habits();
      const lists = await Promise.all(
        myHabits.map((habit) => api.habitPartners(habit.id)),
      );
      setHabits(myHabits);
      setSent(lists.flat());
      setRequests(await api.partnerRequests());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function run(action: () => Promise<string>) {
    setError(null);
    setMessage(null);
    try {
      setMessage(await action());
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "That did not work");
    }
  }

  function sendInvite(event: React.FormEvent) {
    event.preventDefault();
    if (invite.habitId === "") return;
    void run(async () => {
      const partnership = await api.invitePartner(
        Number(invite.habitId),
        invite.email,
      );
      setInvite(EMPTY_INVITE);
      setInviting(false);
      return `Invite sent to ${partnership.partner_display_name}. You will get a notification when they answer.`;
    });
  }

  if (loading) return <p className="muted">Loading…</p>;

  return (
    <div className="stack">
      <div className="spread">
        <div>
          <h2 style={{ margin: 0 }}>Buddies</h2>
          <p className="muted" style={{ margin: 0 }}>
            A buddy sees it when your streak breaks, and you see it when theirs
            does. Nothing is shared until they accept.
          </p>
        </div>
        <button
          className={inviting ? "secondary" : ""}
          onClick={() => setInviting((open) => !open)}
          disabled={habits.length === 0}
        >
          {inviting ? "Cancel" : "🤝 Invite a buddy"}
        </button>
      </div>

      {message && <p className="notice">{message}</p>}
      {error && <p className="error">{error}</p>}
      {habits.length === 0 && (
        <p className="card muted">Add a habit on the Habits page first.</p>
      )}

      {/* The invite form, only when asked for */}
      {inviting && (
        <form className="card accent stack" onSubmit={sendInvite}>
          <strong>Invite a buddy</strong>
          <p className="muted" style={{ margin: 0 }}>
            They need a Buddy Duckling account already — use the email they
            signed up with.
          </p>
          <div className="row" style={{ flexWrap: "wrap" }}>
            <label style={{ marginBottom: 0, flex: "1 1 170px" }}>
              <span>Which habit of yours?</span>
              <select
                value={invite.habitId}
                onChange={(event) =>
                  setInvite({
                    ...invite,
                    habitId: event.target.value ? Number(event.target.value) : "",
                  })
                }
                required
              >
                <option value="">Choose a habit</option>
                {habits.map((habit) => (
                  <option key={habit.id} value={habit.id}>
                    {habit.name}
                  </option>
                ))}
              </select>
            </label>
            <label style={{ marginBottom: 0, flex: "1 1 200px" }}>
              <span>Their email</span>
              <input
                type="email"
                placeholder="their@email.com"
                value={invite.email}
                onChange={(event) =>
                  setInvite({ ...invite, email: event.target.value })
                }
                required
              />
            </label>
          </div>
          <button type="submit">Send invite</button>
        </form>
      )}

      {/* One card per request waiting for me */}
      {requests.length > 0 && (
        <section className="stack">
          <h3 style={{ margin: 0 }}>Waiting for your answer</h3>
          <div className="card-grid">
            {requests.map((request) => (
              <article key={request.id} className="card accent stack">
                <div className="row">
                  <DuckAvatar code={request.owner_avatar} size={56} />
                  <div>
                    <strong>{request.owner_display_name}</strong>
                    <p className="muted" style={{ margin: 0 }}>
                      wants you as a buddy for <b>{request.habit_name}</b>
                    </p>
                  </div>
                </div>

                <label style={{ marginBottom: 0 }}>
                  <span>Pair a habit of yours (needed for shared goals)</span>
                  <select
                    value={pairWith[request.id] ?? ""}
                    onChange={(event) =>
                      setPairWith({
                        ...pairWith,
                        [request.id]: event.target.value
                          ? Number(event.target.value)
                          : "",
                      })
                    }
                  >
                    <option value="">Just keep an eye on them</option>
                    {habits.map((habit) => (
                      <option key={habit.id} value={habit.id}>
                        {habit.name}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="row">
                  <button
                    onClick={() =>
                      run(async () => {
                        const chosen = pairWith[request.id];
                        await api.acceptPartnership(
                          request.id,
                          chosen === "" || chosen === undefined
                            ? null
                            : Number(chosen),
                        );
                        return `You and ${request.owner_display_name} are buddies now.`;
                      })
                    }
                  >
                    Accept
                  </button>
                  <button
                    className="ghost"
                    onClick={() =>
                      run(async () => {
                        await api.declinePartnership(request.id);
                        return "Request declined.";
                      })
                    }
                  >
                    No thanks
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      {/* One card per buddy, with that pair's goals inside it */}
      <section className="stack">
        <h3 style={{ margin: 0 }}>Your buddies</h3>
        {sent.length === 0 ? (
          <p className="card muted">
            No buddies yet. Invite someone to one of your habits.
          </p>
        ) : (
          sent.map((partnership) => (
            <article key={partnership.id} className="card stack buddy-card">
              <div className="spread">
                <div className="row">
                  <DuckAvatar code={partnership.partner_avatar} size={52} />
                  <div>
                    <strong>{partnership.partner_display_name}</strong>
                    <p className="muted" style={{ margin: 0 }}>
                      {partnership.partner_email}
                    </p>
                  </div>
                </div>
                <div className="row">
                  <span className={`pill ${STATUS[partnership.status].tone}`}>
                    {STATUS[partnership.status].label}
                  </span>
                  <button
                    className="ghost"
                    onClick={() =>
                      run(async () => {
                        await api.endPartnership(partnership.id);
                        return "Partnership removed.";
                      })
                    }
                  >
                    Remove
                  </button>
                </div>
              </div>

              <div className="pair-row">
                <span className="pill blue">You · {partnership.habit_name}</span>
                <span className="muted">↔</span>
                <span className="pill">
                  {partnership.partner_display_name} ·{" "}
                  {partnership.partner_habit_name ?? "no habit paired"}
                </span>
              </div>

              {partnership.status === "accepted" && (
                <GoalList
                  title="Shared goals"
                  yourLabel={partnership.habit_name}
                  buddyLabel={`${partnership.partner_display_name} · ${
                    partnership.partner_habit_name ?? "no habit paired"
                  }`}
                  partnershipId={partnership.id}
                  paired={partnership.partner_habit_id !== null}
                  onChange={load}
                />
              )}
            </article>
          ))
        )}
      </section>
    </div>
  );
}
