import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { api } from "../api/client";
import type { AvatarCode } from "../api/types";
import { AvatarPicker } from "../components/AvatarPicker";
import { Duckling } from "../components/Duckling";
import { useAuth } from "../auth/AuthContext";

// Whatever the browser says, with a sensible fallback.
const localTimezone =
  Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Bangkok";

export function RegisterPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    display_name: "",
    email: "",
    password: "",
  });
  const [avatar, setAvatar] = useState<AvatarCode>("clover");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function update(field: keyof typeof form) {
    return (event: React.ChangeEvent<HTMLInputElement>) =>
      setForm({ ...form, [field]: event.target.value });
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.register({ ...form, avatar, timezone: localTimezone });
      await login(form.email, form.password);
      navigate("/");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not sign up");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="center-page">
      <div className="card stack" style={{ width: "min(440px, 100%)" }}>
        <div style={{ textAlign: "center" }}>
          <Duckling size={72} />
          <h1>Create an account</h1>
          <p className="muted">Your streaks will be counted in {localTimezone}.</p>
        </div>

        <form onSubmit={handleSubmit}>
          <label>
            <span>Display name</span>
            <input value={form.display_name} onChange={update("display_name")} required />
          </label>
          <label>
            <span>Email</span>
            <input type="email" value={form.email} onChange={update("email")} required />
          </label>
          <label>
            <span>Password (at least 8 characters)</span>
            <input
              type="password"
              value={form.password}
              onChange={update("password")}
              minLength={8}
              required
            />
          </label>

          <div style={{ marginBottom: "0.9rem" }}>
            <span className="muted">Pick your duckling</span>
            <AvatarPicker value={avatar} onChange={setAvatar} size={48} />
          </div>

          {error && <p className="error">{error}</p>}

          <button type="submit" disabled={busy} style={{ width: "100%" }}>
            {busy ? "Creating…" : "Create account"}
          </button>
        </form>

        <p className="muted" style={{ textAlign: "center", margin: 0 }}>
          Already have one? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
