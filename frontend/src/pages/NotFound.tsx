import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">
      <div className="text-center">
        <p className="text-sm font-medium text-primary">404</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">Page not found</h1>
        <p className="mt-2 text-muted-foreground">This route doesn&apos;t exist in Verba.</p>
        <Link to="/" className="mt-6 inline-block text-sm text-primary hover:underline">
          Back to home
        </Link>
      </div>
    </div>
  );
}
