import { useState, type FormEvent } from "react";

import { api } from "../api/client";
import type { AvatarCode } from "../api/types";
import { AvatarPicker } from "../components/AvatarPicker";
import { DuckAvatar } from "../components/DuckAvatar";
import { useAuth } from "../auth/AuthContext";

export function ProfilePage() {
  const { user, setUser } = useAuth();
  const [displayName, setDisplayName] = useState(user?.display_name ?? "");
  const [avatar, setAvatar] = useState<AvatarCode>(user?.avatar ?? "clover");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!user) return null;

  const unchanged = displayName === user.display_name && avatar === user.avatar;

  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    setError(null);
    try {
      setUser(await api.updateMe({ display_name: displayName, avatar }));
      setMessage("Profile saved.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not save");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack">
      <div>
        <h2 style={{ margin: 0 }}>Your profile</h2>
        <p className="muted" style={{ margin: 0 }}>
          This is how your buddies see you.
        </p>
      </div>

      <form className="card stack" onSubmit={save}>
        <div className="row">
          {/* Live preview of what is about to be saved. */}
          <DuckAvatar code={avatar} size={88} />
          <div style={{ flex: 1 }}>
            <label style={{ marginBottom: 0 }}>
              <span>Display name</span>
              <input
                value={displayName}
                onChange={(event) => setDisplayName(event.target.value)}
                maxLength={100}
                required
              />
            </label>
            <p className="muted" style={{ marginBottom: 0 }}>
              {user.email} · {user.timezone}
            </p>
          </div>
        </div>

        <div>
          <span className="muted">Pick your duckling</span>
          <AvatarPicker value={avatar} onChange={setAvatar} />
        </div>

        {message && <p className="notice">{message}</p>}
        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={busy || unchanged}>
          {busy ? "Saving…" : unchanged ? "Nothing to save" : "Save profile"}
        </button>
      </form>
    </div>
  );
}
