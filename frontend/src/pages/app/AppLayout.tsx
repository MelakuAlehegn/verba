import { SquarePen } from "lucide-react";
import { Link, Outlet } from "react-router-dom";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { UserMenu } from "@/components/layout/UserMenu";
import { Button } from "@/components/ui/button";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";

export default function AppLayout() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="h-svh overflow-hidden">
        <header className="flex h-14 shrink-0 items-center justify-between gap-2 border-b border-border/60 px-4">
          <SidebarTrigger className="text-muted-foreground" />
          <div className="flex items-center gap-2">
            <Button asChild size="sm" className="gap-2 rounded-lg">
              <Link to="/app">
                <SquarePen className="h-4 w-4" />
                New chat
              </Link>
            </Button>
            <ThemeToggle />
            <UserMenu variant="avatar" />
          </div>
        </header>
        <div className="flex flex-1 flex-col overflow-auto">
          <Outlet />
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
