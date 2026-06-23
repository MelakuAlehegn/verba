import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getSettings, updateSettings } from "@/lib/api/settings";
import type { Settings } from "@/lib/api/types";

export const settingsQueryKey = ["settings"] as const;

export function useSettings() {
  return useQuery({ queryKey: settingsQueryKey, queryFn: getSettings });
}

export function useUpdateSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateSettings,
    onSuccess: (settings: Settings) => queryClient.setQueryData(settingsQueryKey, settings),
  });
}
