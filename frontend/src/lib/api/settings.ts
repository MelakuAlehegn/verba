import { apiClient } from "@/lib/api/client";
import type { Settings, SettingsUpdate } from "@/lib/api/types";

export function getSettings(): Promise<Settings> {
  return apiClient<Settings>("/settings");
}

export function updateSettings(data: SettingsUpdate): Promise<Settings> {
  return apiClient<Settings>("/settings", { method: "PATCH", body: data });
}
