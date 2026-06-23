import { env } from "@/config/env";
import { apiClient, ApiError } from "@/lib/api/client";
import type { LoginRequest, RegisterRequest, User } from "@/lib/api/types";

export async function register(data: RegisterRequest): Promise<User> {
  return apiClient<User>("/auth/register", {
    method: "POST",
    body: data,
    suppressUnauthorized: true,
  });
}

export async function login(data: LoginRequest): Promise<User> {
  return apiClient<User>("/auth/login", {
    method: "POST",
    body: data,
    suppressUnauthorized: true,
  });
}

export async function getMe(): Promise<User | null> {
  try {
    return await apiClient<User>("/auth/me", { suppressUnauthorized: true });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return null;
    }
    throw error;
  }
}

export interface UserUpdate {
  name?: string | null;
  avatar_url?: string | null;
  onboarded?: boolean;
}

export async function updateMe(data: UserUpdate): Promise<User> {
  return apiClient<User>("/auth/me", { method: "PATCH", body: data });
}

export async function logout(): Promise<void> {
  await apiClient<void>("/auth/logout", { method: "POST", suppressUnauthorized: true });
}

export function getGoogleAuthUrl(): string {
  return `${env.apiUrl}/auth/google`;
}
