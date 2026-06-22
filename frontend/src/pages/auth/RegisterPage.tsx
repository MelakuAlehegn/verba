import { Link } from "react-router-dom";
import { ThemeToggle } from "@/components/common/ThemeToggle";

export default function RegisterPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-6">
      <div className="absolute right-6 top-6">
        <ThemeToggle />
      </div>
      <h1 className="text-2xl font-semibold tracking-tight">Create your Verba account</h1>
      <p className="text-sm text-muted-foreground">Auth UI ships in F2.</p>
      <Link to="/login" className="text-sm text-primary hover:underline">
        Already have an account? Sign in
      </Link>
    </div>
  );
}
