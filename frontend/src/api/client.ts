import type {
  AppNotification,
  AvatarCode,
  AvatarOption,
  Dashboard,
  Habit,
  HabitLog,
  HabitLogCreated,
  HabitStats,
  Partnership,
  PersonalGoal,
  SharedGoal,
  TokenPair,
  User,
  UserBadge,
} from "./types";

const TOKEN_KEY = "buddy-duckling-tokens";

export interface StoredTokens {
  access_token: string;
  refresh_token: string;
}

export function readTokens(): StoredTokens | null {
  const raw = localStorage.getItem(TOKEN_KEY);
  return raw ? (JSON.parse(raw) as StoredTokens) : null;
}

export function writeTokens(tokens: StoredTokens | null): void {
  if (tokens) {
    localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function readError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    // FastAPI sends a string for our own errors and a list for validation ones.
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) return body.detail[0]?.msg ?? "Invalid input";
  } catch {
    /* fall through to the generic message */
  }
  return "Something went wrong";
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  retryOn401 = true,
): Promise<T> {
  const tokens = readTokens();

  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(tokens ? { Authorization: `Bearer ${tokens.access_token}` } : {}),
        ...options.headers,
      },
    });
  } catch {
    // fetch only rejects when the request never reached the server at all.
    throw new ApiError(0, "Cannot reach the server - is the API running?");
  }

  // An expired access token is normal after 30 minutes: swap it for a fresh one
  // with the refresh token and replay the request once.
  if (response.status === 401 && retryOn401 && tokens?.refresh_token) {
    const refreshed = await refresh(tokens.refresh_token);
    if (refreshed) return request<T>(path, options, false);
  }

  if (!response.ok) throw new ApiError(response.status, await readError(response));
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

async function refresh(refreshToken: string): Promise<boolean> {
  const response = await fetch("/api/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!response.ok) {
    writeTokens(null);
    return false;
  }
  const tokens = (await response.json()) as TokenPair;
  writeTokens(tokens);
  return true;
}

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body ?? {}) });
const put = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "PUT", body: JSON.stringify(body ?? {}) });

export const api = {
  register: (body: {
    email: string;
    password: string;
    display_name: string;
    timezone: string;
    avatar: AvatarCode;
  }) => post<User>("/auth/register", body),

  avatars: () => request<AvatarOption[]>("/avatars"),

  login: async (email: string, password: string) => {
    const tokens = await post<TokenPair>("/auth/login", { email, password });
    writeTokens(tokens);
    return tokens;
  },

  logout: () => writeTokens(null),

  me: () => request<User>("/users/me"),
  updateMe: (body: {
    display_name?: string;
    timezone?: string;
    avatar?: AvatarCode;
  }) => put<User>("/users/me", body),

  dashboard: () => request<Dashboard>("/me/dashboard"),

  habits: () => request<Habit[]>("/habits"),
  createHabit: (body: {
    name: string;
    description?: string | null;
    frequency_type: string;
    frequency_target: number;
  }) => post<Habit>("/habits", body),
  habit: (id: number) => request<Habit>(`/habits/${id}`),
  updateHabit: (id: number, body: { name?: string; is_active?: boolean }) =>
    put<Habit>(`/habits/${id}`, body),
  deleteHabit: (id: number) =>
    request<void>(`/habits/${id}`, { method: "DELETE" }),

  logHabit: (id: number) => post<HabitLogCreated>(`/habits/${id}/logs`),
  habitLogs: (id: number) => request<HabitLog[]>(`/habits/${id}/logs`),
  habitStats: (id: number) => request<HabitStats>(`/habits/${id}/stats`),

  notifications: () => request<AppNotification[]>("/me/notifications"),
  markNotificationRead: (id: number) =>
    put<AppNotification>(`/notifications/${id}/read`),
  markAllNotificationsRead: () => put<{ unread: number }>("/me/notifications/read-all"),

  badges: () => request<UserBadge[]>("/me/badges"),

  // Personal goals
  myGoals: () => request<PersonalGoal[]>("/me/goals"),
  habitGoals: (habitId: number) =>
    request<PersonalGoal[]>(`/habits/${habitId}/goals`),
  createPersonalGoal: (
    habitId: number,
    body: {
      title: string;
      target_days?: number | null;
      reward_description?: string | null;
    },
  ) => post<PersonalGoal>(`/habits/${habitId}/goals`, body),
  deletePersonalGoal: (habitId: number, goalId: number) =>
    request<void>(`/habits/${habitId}/goals/${goalId}`, { method: "DELETE" }),

  // Buddies
  habitPartners: (habitId: number) =>
    request<Partnership[]>(`/habits/${habitId}/partners`),
  invitePartner: (habitId: number, partnerEmail: string) =>
    post<Partnership>(`/habits/${habitId}/partners`, { partner_email: partnerEmail }),
  partnerRequests: () => request<Partnership[]>("/me/partner-requests"),
  acceptPartnership: (id: number, partnerHabitId: number | null) =>
    put<Partnership>(`/partners/${id}/accept`, { partner_habit_id: partnerHabitId }),
  declinePartnership: (id: number) => put<Partnership>(`/partners/${id}/decline`),
  endPartnership: (id: number) =>
    request<void>(`/partners/${id}`, { method: "DELETE" }),

  // Shared goals
  goals: (partnershipId: number) =>
    request<SharedGoal[]>(`/partnerships/${partnershipId}/goals`),
  createGoal: (
    partnershipId: number,
    body: {
      title: string;
      reward_description?: string | null;
      duration_days: number;
      target_streak_a?: number | null;
      target_streak_b?: number | null;
    },
  ) => post<SharedGoal>(`/partnerships/${partnershipId}/goals`, body),
  deleteGoal: (partnershipId: number, goalId: number) =>
    request<void>(`/partnerships/${partnershipId}/goals/${goalId}`, {
      method: "DELETE",
    }),
};
