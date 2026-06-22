import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "@/features/auth/context/AuthContext";

export function RedirectIfAuthed() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  if (isAuthenticated) {
    return <Navigate to="/app" replace />;
  }

  return <Outlet />;
}
