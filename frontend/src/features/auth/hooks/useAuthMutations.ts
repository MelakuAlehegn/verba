import { useMutation } from "@tanstack/react-query";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/features/auth/context/AuthContext";
import { getPostAuthPath } from "@/features/auth/utils";
import type { LoginFormValues, RegisterFormValues } from "@/features/auth/schemas";
import { login, register } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";

function resolvePostAuthDestination(
  user: { onboarded_at: string | null },
  fromPath?: string,
): string {
  if (!user.onboarded_at) {
    return "/onboarding";
  }
  return fromPath ?? "/app";
}

export function useLoginMutation() {
  const { setUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  return useMutation({
    mutationFn: (values: LoginFormValues) => login(values),
    onSuccess: (user) => {
      setUser(user);
      const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      navigate(resolvePostAuthDestination(user, from), { replace: true });
    },
  });
}

export function useRegisterMutation() {
  const { setUser } = useAuth();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (values: RegisterFormValues) =>
      register({
        email: values.email,
        password: values.password,
        name: values.name?.trim() || null,
      }),
    onSuccess: (user) => {
      setUser(user);
      navigate(getPostAuthPath(user), { replace: true });
    },
  });
}

export function getAuthErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    return error.message || fallback;
  }
  return fallback;
}
