import { Outlet } from "react-router-dom";
import { ThemeToggle } from "@/components/common/ThemeToggle";

export default function AppLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="flex items-center justify-between border-b px-6 py-4">
        <span className="text-sm font-semibold tracking-tight">Verba</span>
        <ThemeToggle />
      </header>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}
