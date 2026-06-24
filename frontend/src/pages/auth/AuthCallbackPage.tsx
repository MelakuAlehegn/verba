import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/context/AuthContext";
import { getPostAuthPath } from "@/features/auth/utils";

export default function AuthCallbackPage() {
  const { refreshUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState<string | null>(searchParams.get("error"));

  useEffect(() => {
    if (error) return;

    let cancelled = false;

    refreshUser()
      .then((user) => {
        if (cancelled) return;
        if (!user) {
          setError("Sign-in could not be completed. Please try again.");
          return;
        }
        navigate(getPostAuthPath(user), { replace: true });
      })
      .catch(() => {
        if (!cancelled) {
          setError("Sign-in could not be completed. Please try again.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [error, navigate, refreshUser]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center px-6">
        <div className="w-full max-w-md space-y-4">
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <Button asChild className="w-full rounded-lg">
            <Link to="/login">Back to sign in</Link>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center text-muted-foreground">
      Completing sign-in…
    </div>
  );
}
