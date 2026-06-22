import type { User } from "@/lib/api/types";

export const authQueryKey = ["auth", "me"] as const;

export function getPostAuthPath(user: User, fallback = "/app"): string {
  if (!user.onboarded_at) {
    return "/onboarding";
  }
  return fallback;
}
