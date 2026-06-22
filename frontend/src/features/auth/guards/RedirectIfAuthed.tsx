import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "@/features/auth/context/AuthContext";
import { getPostAuthPath } from "@/features/auth/utils";

export function RedirectIfAuthed() {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        Loading…
      </div>
    );
  }

  if (isAuthenticated && user) {
    return <Navigate to={getPostAuthPath(user)} replace />;
  }

  return <Outlet />;
}
