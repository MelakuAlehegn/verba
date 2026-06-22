import { Bell, FileText, MessageSquareText, Plus, Quote, Settings } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { ChatList } from "@/features/chats/components/ChatList";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { UserMenu } from "@/components/layout/UserMenu";
import { Button } from "@/components/ui/button";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";

interface NavEntry {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
}

const NAV: NavEntry[] = [
  { to: "/app", label: "Ask", icon: MessageSquareText, end: true },
  { to: "/app/documents", label: "Documents", icon: FileText },
  { to: "/app/settings", label: "Settings", icon: Settings },
];

function NavItem({ entry }: { entry: NavEntry }) {
  const { pathname } = useLocation();
  const isActive = entry.end
    ? pathname === entry.to
    : pathname === entry.to || pathname.startsWith(`${entry.to}/`);

  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild isActive={isActive} tooltip={entry.label}>
        <NavLink to={entry.to} end={entry.end}>
          <entry.icon />
          <span>{entry.label}</span>
        </NavLink>
      </SidebarMenuButton>
    </SidebarMenuItem>
  );
}

export function AppSidebar() {
  const navigate = useNavigate();
  const { isMobile, setOpenMobile } = useSidebar();

  const startNewChat = () => {
    // F5 will create the chat lazily on first message; for now, open the canvas.
    navigate("/app");
    if (isMobile) setOpenMobile(false);
  };

  return (
    <Sidebar>
      <SidebarHeader className="gap-3 p-3">
        <NavLink to="/app" className="flex items-center gap-2 px-1 py-1">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[image:var(--gradient-primary)] text-primary-foreground shadow-[var(--shadow-primary)]">
            <Quote className="h-4 w-4" />
          </span>
          <span className="text-base font-semibold tracking-tight">Verba</span>
        </NavLink>
        <Button onClick={startNewChat} className="w-full justify-start gap-2 rounded-xl">
          <Plus className="h-4 w-4" />
          New chat
        </Button>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {NAV.map((entry) => (
                <NavItem key={entry.to} entry={entry} />
              ))}
              <SidebarMenuItem>
                <SidebarMenuButton
                  tooltip="Notifications"
                  onClick={() => toast("Notifications are coming soon.")}
                >
                  <Bell />
                  <span>Notifications</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Your chats</SidebarGroupLabel>
          <SidebarGroupContent>
            <ChatList />
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="gap-2">
        <div className="flex items-center justify-between px-1">
          <span className="text-xs text-muted-foreground">Theme</span>
          <ThemeToggle />
        </div>
        <UserMenu />
      </SidebarFooter>
    </Sidebar>
  );
}
