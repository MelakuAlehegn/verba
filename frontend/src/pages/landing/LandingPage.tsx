import { ArrowUp, FileUp, MessagesSquare, Quote, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { Button } from "@/components/ui/button";

export const LANDING_INTENT_KEY = "verba:intent";

const STEPS = [
  { icon: FileUp, title: "Upload your documents", body: "PDF, Word, text, or Markdown — drop them in." },
  { icon: MessagesSquare, title: "Ask in plain language", body: "Question your files like a conversation." },
  { icon: Quote, title: "Get cited answers", body: "Every answer shows the exact passages it used." },
];

const EXAMPLES = ["Summarize this contract", "What are the key dates?", "List the action items"];

function HeroPrompt() {
  const navigate = useNavigate();
  const [value, setValue] = useState("");

  const submit = () => {
    const trimmed = value.trim();
    if (trimmed) sessionStorage.setItem(LANDING_INTENT_KEY, trimmed);
    navigate("/register");
  };

  return (
    <div className="mx-auto mt-10 w-full max-w-xl">
      <div className="flex items-end gap-2 rounded-xl border border-border bg-card p-2 shadow-sm focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-ring">
        <textarea
          rows={1}
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              submit();
            }
          }}
          placeholder="Ask your documents…"
          className="max-h-32 flex-1 resize-none bg-transparent px-3 py-2 text-sm outline-none placeholder:text-muted-foreground"
          aria-label="Ask your documents"
        />
        <Button size="icon" className="h-9 w-9 shrink-0 rounded-lg" onClick={submit} aria-label="Get started">
          <ArrowUp className="h-4 w-4" />
        </Button>
      </div>
      <div className="mt-4 flex flex-wrap justify-center gap-2">
        {EXAMPLES.map((example) => (
          <button
            key={example}
            type="button"
            onClick={() => setValue(example)}
            className="rounded-full border border-border bg-card/60 px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
          >
            {example}
          </button>
        ))}
      </div>
      <p className="mt-4 flex items-center justify-center gap-1.5 text-xs text-muted-foreground">
        <ShieldCheck className="h-3.5 w-3.5" />
        Free to start — your documents stay private to you.
      </p>
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      <div
        className="pointer-events-none absolute inset-0"
        aria-hidden
        style={{
          backgroundImage: `
            linear-gradient(to right, hsl(var(--muted-foreground) / 0.09) 1px, transparent 1px),
            linear-gradient(to bottom, hsl(var(--muted-foreground) / 0.09) 1px, transparent 1px)
          `,
          backgroundSize: "44px 44px",
          // Peak around the middle, fading toward the top and edges.
          maskImage: "radial-gradient(ellipse 75% 55% at 50% 46%, black 0%, transparent 72%)",
          WebkitMaskImage: "radial-gradient(ellipse 75% 55% at 50% 46%, black 0%, transparent 72%)",
        }}
      />
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-[420px] bg-gradient-to-b from-primary/[0.06] via-transparent to-transparent dark:from-primary/10"
        aria-hidden
      />
      {/* Soft emerald halo behind the prompt — draws the eye to the centerpiece. */}
      <div
        className="pointer-events-none absolute left-1/2 top-[300px] h-72 w-[42rem] max-w-[90vw] -translate-x-1/2 rounded-full bg-primary/20 blur-[120px] dark:bg-primary/25"
        aria-hidden
      />

      <header className="relative z-10 mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">
        <span className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[image:var(--gradient-primary)] text-primary-foreground">
            <Quote className="h-4 w-4" />
          </span>
          <span className="text-lg font-semibold tracking-tight">Verba</span>
        </span>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button asChild variant="ghost" size="sm" className="rounded-lg">
            <Link to="/login">Sign in</Link>
          </Button>
          <Button asChild size="sm" className="rounded-lg">
            <Link to="/register">Get started</Link>
          </Button>
        </div>
      </header>

      <main className="relative z-10 mx-auto w-full max-w-3xl px-6 pb-24 pt-20 text-center sm:pt-28">
        <p className="mb-4 text-sm font-medium tracking-wide text-primary">Document Q&amp;A</p>
        <h1 className="animate-fade-in text-balance text-4xl font-semibold tracking-tight sm:text-5xl sm:leading-[1.1]">
          Ask your <span className="text-primary">documents</span> anything.
        </h1>
        <p className="animate-slide-up mx-auto mt-5 max-w-xl text-balance text-base leading-relaxed text-muted-foreground sm:text-lg">
          Upload your files and get streamed answers grounded in your sources — with citations you
          can trust.
        </p>

        <HeroPrompt />

        <section className="mt-24 grid gap-6 text-left sm:grid-cols-3">
          {STEPS.map((step) => (
            <div key={step.title} className="rounded-xl border border-border bg-card/60 p-5">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary text-primary">
                <step.icon className="h-4 w-4" />
              </span>
              <h2 className="mt-3 font-medium">{step.title}</h2>
              <p className="mt-1 text-sm text-muted-foreground">{step.body}</p>
            </div>
          ))}
        </section>
      </main>

      <footer className="relative z-10 mx-auto w-full max-w-6xl px-6 py-8 text-center text-xs text-muted-foreground">
        © 2026 Verba
      </footer>
    </div>
  );
}
