export type AvatarCode =
  | "clover"
  | "nerd"
  | "bow"
  | "adventurer"
  | "foodie"
  | "chill";

export interface AvatarOption {
  code: AvatarCode;
  title: string;
  description: string;
}

export type FrequencyType = "daily" | "weekly_n_times";

export interface User {
  id: number;
  email: string;
  display_name: string;
  avatar: AvatarCode;
  timezone: string;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Habit {
  id: number;
  user_id: number;
  name: string;
  description: string | null;
  frequency_type: FrequencyType;
  frequency_target: number;
  current_streak: number;
  longest_streak: number;
  is_active: boolean;
  created_at: string;
}

export interface HabitLog {
  id: number;
  habit_id: number;
  logged_at_utc: string;
  log_date_local: string;
}

export interface HabitLogCreated {
  log: HabitLog;
  current_streak: number;
  longest_streak: number;
}

export interface DashboardHabit {
  habit_id: number;
  name: string;
  frequency_type: FrequencyType;
  current_streak: number;
  longest_streak: number;
  logged_today: boolean;
}

export interface Dashboard {
  display_name: string;
  avatar: AvatarCode;
  timezone: string;
  today_local: string;
  active_habits: number;
  logged_today: number;
  habits: DashboardHabit[];
  badges_earned: number;
  unread_notifications: number;
  pending_partner_requests: number;
  accepted_partnerships: number;
  active_shared_goals: number;
}

export interface HabitStats {
  habit_id: number;
  name: string;
  frequency_type: FrequencyType;
  frequency_target: number;
  current_streak: number;
  longest_streak: number;
  total_logs: number;
  first_log_date: string | null;
  last_log_date: string | null;
  logged_today: boolean;
  completion_rate_30d: number;
  logs_this_week: number;
}

export type PartnershipStatus = "pending" | "accepted" | "declined";

export interface Partnership {
  id: number;
  status: PartnershipStatus;
  created_at: string;
  habit_id: number;
  habit_name: string;
  owner_user_id: number;
  owner_display_name: string;
  owner_avatar: AvatarCode;
  partner_user_id: number;
  partner_display_name: string;
  partner_email: string;
  partner_avatar: AvatarCode;
  partner_habit_id: number | null;
  partner_habit_name: string | null;
}

export interface Milestone {
  percent: number;
  days: number;
  reached: boolean;
}

export interface SharedGoal {
  id: number;
  partnership_id: number;
  title: string;
  reward_description: string | null;
  duration_days: number;
  target_streak_a: number;
  target_streak_b: number;
  achieved_at: string | null;
  created_at: string;
  current_streak_a: number;
  current_streak_b: number;
  reached_a: boolean;
  reached_b: boolean;
  joint_days: number;
  joint_percent: number;
  days_remaining: number;
  milestones: Milestone[];
  my_side: "a" | "b" | "none";
}

export type NotificationType =
  | "streak_broken"
  | "partner_request"
  | "partner_accepted"
  | "partner_declined"
  | "waiting_for_partner"
  | "goal_achieved"
  | "badge_earned";

export interface AppNotification {
  id: number;
  type: NotificationType;
  title: string;
  body: string;
  related_habit_id: number | null;
  related_partnership_id: number | null;
  is_read: boolean;
  created_at: string;
}

export interface Badge {
  code: string;
  title: string;
  milestone_days: number;
}

export interface UserBadge {
  id: number;
  habit_id: number;
  earned_at: string;
  badge: Badge;
}
