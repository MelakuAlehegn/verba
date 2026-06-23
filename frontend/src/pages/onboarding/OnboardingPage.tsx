import { ArrowRight, Check, FileText, Sparkles, UserRound } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { StatusBadge } from "@/features/documents/components/StatusBadge";
import { UploadDropzone } from "@/features/documents/components/UploadDropzone";
import { useDocuments } from "@/features/documents/hooks";
import { useAuth } from "@/features/auth/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { updateMe } from "@/lib/api/auth";

const STEPS = ["Welcome", "Profile", "Documents", "Done"];

export default function OnboardingPage() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const { data: documents } = useDocuments();

  const [step, setStep] = useState(0);
  const [name, setName] = useState(user?.name ?? "");
  const [saving, setSaving] = useState(false);

  const saveName = async () => {
    const trimmed = name.trim();
    if (trimmed && trimmed !== user?.name) {
      setSaving(true);
      try {
        setUser(await updateMe({ name: trimmed }));
      } catch {
        toast.error("Couldn't save your name. You can change it later in Settings.");
      } finally {
        setSaving(false);
      }
    }
    setStep(2);
  };

  const finish = async () => {
    setSaving(true);
    try {
      setUser(await updateMe({ onboarded: true }));
      navigate("/app", { replace: true });
    } catch {
      toast.error("Something went wrong. Try again.");
      setSaving(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6 py-12">
      <div className="w-full max-w-md">
        {/* Step indicator */}
        <div className="mb-10 flex items-center justify-center gap-2">
          {STEPS.map((label, index) => (
            <div key={label} className="flex items-center gap-2">
              <span
                className={[
                  "flex h-7 w-7 items-center justify-center rounded-full text-xs font-medium transition-colors",
                  index < step
                    ? "bg-primary text-primary-foreground"
                    : index === step
                      ? "bg-primary/15 text-primary ring-1 ring-primary"
                      : "bg-muted text-muted-foreground",
                ].join(" ")}
              >
                {index < step ? <Check className="h-3.5 w-3.5" /> : index + 1}
              </span>
              {index < STEPS.length - 1 ? <span className="h-px w-6 bg-border" /> : null}
            </div>
          ))}
        </div>

        {step === 0 ? (
          <div className="text-center">
            <span className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-secondary text-primary">
              <Sparkles className="h-6 w-6" />
            </span>
            <h1 className="text-2xl font-semibold tracking-tight">
              Welcome to Verba{user?.name ? `, ${user.name.split(" ")[0]}` : ""}
            </h1>
            <p className="mx-auto mt-3 max-w-sm text-muted-foreground">
              Upload your documents and ask questions — Verba answers from your files and shows the
              exact passages it used. Let's set you up in a few steps.
            </p>
            <Button className="mt-8 w-full gap-2 rounded-xl" onClick={() => setStep(1)}>
              Get started <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        ) : step === 1 ? (
          <div>
            <span className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-secondary text-primary">
              <UserRound className="h-6 w-6" />
            </span>
            <h1 className="text-2xl font-semibold tracking-tight">What should we call you?</h1>
            <p className="mt-2 text-muted-foreground">This shows on your profile. You can change it anytime.</p>
            <div className="mt-6 space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Your name"
                className="h-11 rounded-xl"
              />
            </div>
            <Button className="mt-8 w-full gap-2 rounded-xl" onClick={saveName} disabled={saving}>
              Continue <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        ) : step === 2 ? (
          <div>
            <span className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-secondary text-primary">
              <FileText className="h-6 w-6" />
            </span>
            <h1 className="text-2xl font-semibold tracking-tight">Add your first document</h1>
            <p className="mt-2 text-muted-foreground">
              Upload a file to ask about. You can skip this and add documents later.
            </p>
            <div className="mt-6">
              <UploadDropzone />
            </div>
            {documents && documents.length > 0 ? (
              <ul className="mt-4 space-y-2">
                {documents.slice(0, 4).map((document) => (
                  <li
                    key={document.id}
                    className="flex items-center justify-between rounded-xl border border-border bg-card px-3 py-2 text-sm"
                  >
                    <span className="truncate pr-2">{document.filename}</span>
                    <StatusBadge status={document.status} />
                  </li>
                ))}
              </ul>
            ) : null}
            <Button className="mt-8 w-full gap-2 rounded-xl" onClick={() => setStep(3)}>
              Continue <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <div className="text-center">
            <span className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
              <Check className="h-6 w-6" />
            </span>
            <h1 className="text-2xl font-semibold tracking-tight">You're all set</h1>
            <p className="mx-auto mt-3 max-w-sm text-muted-foreground">
              Head to your workspace and ask your first question. Verba will answer from your
              documents, with sources.
            </p>
            <Button className="mt-8 w-full rounded-xl" onClick={finish} disabled={saving}>
              Go to dashboard
            </Button>
          </div>
        )}

        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={finish}
            disabled={saving}
            className="text-sm text-muted-foreground hover:text-foreground disabled:opacity-50"
          >
            Skip for now
          </button>
        </div>
      </div>
    </div>
  );
}
