export interface AuthUser {
  id: number;
  username: string;
  email: string | null;
  display_name: string | null;
  avatar_url: string | null;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface MergeDeviceResult {
  word_progress: number;
  scenarios: number;
  attempts: number;
  conversations: number;
  streak: number;
}
