import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { getMe, logout as logoutApi } from "@/lib/api/auth";
import { setUnauthorizedHandler } from "@/lib/api/client";
import type { User } from "@/lib/api/types";
import { authQueryKey } from "@/features/auth/utils";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  refreshUser: () => Promise<User | null>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const { data: user = null, isLoading } = useQuery({
    queryKey: authQueryKey,
    queryFn: getMe,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  const setUser = useCallback(
    (nextUser: User | null) => {
      queryClient.setQueryData(authQueryKey, nextUser);
    },
    [queryClient],
  );

  const refreshUser = useCallback(async () => {
    const result = await queryClient.fetchQuery({
      queryKey: authQueryKey,
      queryFn: getMe,
    });
    return result;
  }, [queryClient]);

  const logout = useCallback(async () => {
    try {
      await logoutApi();
    } finally {
      setUser(null);
      navigate("/login", { replace: true });
    }
  }, [navigate, setUser]);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setUser(null);
      navigate("/login", { replace: true });
    });
    return () => setUnauthorizedHandler(null);
  }, [navigate, setUser]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isAuthenticated: user !== null,
      setUser,
      refreshUser,
      logout,
    }),
    [user, isLoading, setUser, refreshUser, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
