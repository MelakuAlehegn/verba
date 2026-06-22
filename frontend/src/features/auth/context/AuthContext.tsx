import { createContext, useContext, type ReactNode } from "react";

export interface AuthUser {
  id: string;
  email: string;
  name: string | null;
  onboarded_at: string | null;
}

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/** Stub provider — F2 hydrates from GET /auth/me. */
export function AuthProvider({ children }: { children: ReactNode }) {
  const value: AuthContextValue = {
    user: null,
    isLoading: false,
    isAuthenticated: false,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
