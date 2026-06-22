import { Link } from "react-router-dom";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.35] dark:opacity-[0.2]"
        aria-hidden
        style={{
          backgroundImage: `
            linear-gradient(to right, hsl(var(--border) / 0.5) 1px, transparent 1px),
            linear-gradient(to bottom, hsl(var(--border) / 0.5) 1px, transparent 1px)
          `,
          backgroundSize: "48px 48px",
          maskImage: "radial-gradient(ellipse 70% 60% at 50% 0%, black 20%, transparent 70%)",
        }}
      />
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-[420px] bg-gradient-to-b from-primary/8 via-transparent to-transparent dark:from-primary/12"
        aria-hidden
      />

      <header className="relative z-10 mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">
        <Link to="/" className="text-lg font-semibold tracking-tight text-foreground">
          Verba
        </Link>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button asChild size="sm" className="rounded-xl">
            <Link to="/register">Get started</Link>
          </Button>
        </div>
      </header>

      <main className="relative z-10 mx-auto flex w-full max-w-3xl flex-col items-center px-6 pb-24 pt-20 text-center sm:pt-28">
        <p className="mb-4 text-sm font-medium tracking-wide text-primary">Document Q&amp;A</p>
        <h1 className="animate-fade-in text-4xl font-semibold tracking-tight text-foreground sm:text-5xl sm:leading-[1.1]">
          Ask your documents anything
        </h1>
        <p className="animate-slide-up mt-5 max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg">
          Upload your files, ask questions in plain language, and get streamed answers grounded in
          your sources — with citations you can trust.
        </p>
        <div className="animate-slide-up mt-10 flex flex-col gap-3 sm:flex-row">
          <Button asChild size="lg" className="rounded-xl px-8">
            <Link to="/register">Start for free</Link>
          </Button>
          <Button asChild variant="outline" size="lg" className="rounded-xl px-8">
            <Link to="/login">Sign in</Link>
          </Button>
        </div>
      </main>
    </div>
  );
}
