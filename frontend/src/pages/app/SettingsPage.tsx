import { useMutation } from "@tanstack/react-query";
import { Monitor, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useState } from "react";
import { toast } from "sonner";
import { useAuth } from "@/features/auth/context/AuthContext";
import { useSettings, useUpdateSettings } from "@/features/settings/hooks";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { updateMe } from "@/lib/api/auth";
import { cn } from "@/lib/utils";

function Section({ children }: { children: React.ReactNode }) {
  return <div className="space-y-5 rounded-xl border border-border bg-card p-6">{children}</div>;
}

function ProfileTab() {
  const { user, setUser } = useAuth();
  const [name, setName] = useState(user?.name ?? "");

  const save = useMutation({
    mutationFn: () => updateMe({ name: name.trim() }),
    onSuccess: (updated) => {
      setUser(updated);
      toast("Profile saved.");
    },
    onError: () => toast.error("Couldn't save your profile."),
  });

  return (
    <Section>
      <div className="space-y-2">
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Your name"
          className="h-11 max-w-sm rounded-lg"
        />
        <p className="text-xs text-muted-foreground">Shown on your profile in the sidebar.</p>
      </div>
      <Button onClick={() => save.mutate()} disabled={save.isPending} className="rounded-lg">
        Save changes
      </Button>
    </Section>
  );
}

function AccountTab() {
  const { user, logout } = useAuth();
  const { data: settings } = useSettings();
  const updateSettings = useUpdateSettings();

  return (
    <Section>
      <div className="space-y-2">
        <Label>Email</Label>
        <Input value={user?.email ?? ""} disabled className="h-11 max-w-sm rounded-lg" />
      </div>

      <div className="space-y-2">
        <Label>Preferred answer provider</Label>
        <Select
          value={settings?.default_provider}
          onValueChange={(value) => updateSettings.mutate({ default_provider: value })}
        >
          <SelectTrigger className="h-11 max-w-sm rounded-lg">
            <SelectValue placeholder="Select a provider" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="gemini">Gemini</SelectItem>
            <SelectItem value="groq">Groq</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground">
          Which model provider generates your answers.
        </p>
      </div>

      <div className="border-t border-border pt-5">
        <Button variant="outline" className="rounded-lg" onClick={() => void logout()}>
          Sign out
        </Button>
      </div>
    </Section>
  );
}

const THEMES = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Monitor },
];

function AppearanceTab() {
  const { theme, setTheme } = useTheme();

  return (
    <Section>
      <div className="space-y-3">
        <Label>Theme</Label>
        <div className="grid max-w-md grid-cols-3 gap-3">
          {THEMES.map((option) => {
            const active = theme === option.value;
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => setTheme(option.value)}
                className={cn(
                  "flex flex-col items-center gap-2 rounded-lg border p-4 text-sm transition-colors",
                  active
                    ? "border-primary bg-secondary text-foreground ring-1 ring-primary"
                    : "border-border text-muted-foreground hover:bg-secondary/50",
                )}
              >
                <option.icon className="h-5 w-5" />
                {option.label}
              </button>
            );
          })}
        </div>
      </div>
    </Section>
  );
}

export default function SettingsPage() {
  return (
    <div className="mx-auto w-full max-w-2xl px-6 py-8">
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">Settings</h1>
      <Tabs defaultValue="profile">
        <TabsList className="mb-6">
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="account">Account</TabsTrigger>
          <TabsTrigger value="appearance">Appearance</TabsTrigger>
        </TabsList>
        <TabsContent value="profile">
          <ProfileTab />
        </TabsContent>
        <TabsContent value="account">
          <AccountTab />
        </TabsContent>
        <TabsContent value="appearance">
          <AppearanceTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
