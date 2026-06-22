import { FileText } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/context/AuthContext";

export default function AppIndexPage() {
  const { user } = useAuth();
  const firstName = user?.name?.trim().split(/\s+/)[0];

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col items-center justify-center px-6 py-16 text-center">
      <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">
        {firstName ? `Welcome back, ${firstName}` : "Welcome to Verba"}
      </p>
      <h1 className="mt-4 text-balance text-4xl font-semibold tracking-tight sm:text-5xl">
        Ask anything about your documents.
      </h1>
      <p className="mt-4 max-w-md text-balance text-muted-foreground">
        Verba answers from your own files and shows the exact passages it used. Add a
        document to start asking grounded questions.
      </p>
      <div className="mt-8">
        <Button asChild size="lg" className="gap-2 rounded-xl">
          <Link to="/app/documents">
            <FileText className="h-4 w-4" />
            Add your first document
          </Link>
        </Button>
      </div>
    </div>
  );
}
