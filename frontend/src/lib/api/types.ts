export interface User {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  onboarded_at: string | null;
  last_login_at: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name?: string | null;
}
