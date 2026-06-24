import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { cn } from "@/lib/utils";

export function ThemeToggle() {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const current = theme === "system" ? resolvedTheme : theme;

  const option = (value: "light" | "dark", Icon: typeof Sun, label: string) => (
    <button
      type="button"
      onClick={() => setTheme(value)}
      aria-label={label}
      aria-pressed={current === value}
      className={cn(
        "flex h-7 w-7 items-center justify-center rounded-full transition-colors",
        current === value
          ? "bg-secondary text-primary shadow-sm"
          : "text-muted-foreground hover:text-foreground",
      )}
    >
      <Icon className="h-4 w-4" />
    </button>
  );

  return (
    <div className="inline-flex items-center gap-0.5 rounded-full border border-border bg-card p-0.5">
      {option("light", Sun, "Light mode")}
      {option("dark", Moon, "Dark mode")}
    </div>
  );
}
