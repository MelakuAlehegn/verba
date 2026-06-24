import { useState } from "react";
import {
  Settings,
  FileText,
  CheckCircle2,
  XCircle,
  RefreshCw,
  ChevronDown,
  Folder,
  Cpu,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ChatSidebarProps {
  isOpen: boolean;
  onReload: () => void;
  status: {
    assistantReady: boolean;
    documentsLoaded: boolean;
    documentCount: number;
    chunkCount: number;
  };
  documents: string[];
  selectedProvider: string;
  onProviderChange: (provider: string) => void;
  providers: string[];
}

export const ChatSidebar = ({
  isOpen,
  onReload,
  status,
  documents,
  selectedProvider,
  onProviderChange,
  providers,
}: ChatSidebarProps) => {
  const [showDocuments, setShowDocuments] = useState(false);
  const [isReloading, setIsReloading] = useState(false);

  const handleReload = async () => {
    setIsReloading(true);
    await onReload();
    setTimeout(() => setIsReloading(false), 1000);
  };

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 h-full w-72 glass border-r border-border",
        "transform transition-transform duration-300 ease-out z-40",
        "flex flex-col",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}
    >
      {/* Header */}
      <div className="p-5">
        <div className="gradient-primary rounded-lg p-4 text-center shadow-primary">
          <div className="flex items-center justify-center gap-2 mb-1">
            <Settings className="w-5 h-5 text-primary-foreground" />
            <h3 className="font-semibold text-primary-foreground">Settings</h3>
          </div>
          <p className="text-xs text-primary-foreground/80">
            Manage your RAG system
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-5 pb-5 space-y-5">
        {/* System Status */}
        <section>
          <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
            <Cpu className="w-3.5 h-3.5" />
            System Status
          </h4>
          <div className="space-y-2">
            <StatusBadge
              success={status.assistantReady}
              label={status.assistantReady ? "Assistant Ready" : "Assistant Failed"}
            />
            <StatusBadge
              success={status.documentsLoaded}
              label={status.documentsLoaded ? "Documents Loaded" : "No Documents"}
            />
          </div>
        </section>

        {/* Document Management */}
        <section>
          <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
            <FileText className="w-3.5 h-3.5" />
            Document Management
          </h4>

          {status.documentsLoaded && (
            <div className="bg-secondary text-secondary-foreground rounded-lg px-4 py-3 text-center mb-3 border border-primary/20">
              <span className="font-semibold text-sm">
                {status.documentCount} Files • {status.chunkCount} Chunks
              </span>
            </div>
          )}

          {/* Document Sources Accordion */}
          {documents.length > 0 && (
            <button
              onClick={() => setShowDocuments(!showDocuments)}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-muted hover:bg-muted/80 transition-colors text-sm"
            >
              <span className="flex items-center gap-2">
                <Folder className="w-4 h-4 text-muted-foreground" />
                View Sources
              </span>
              <ChevronDown
                className={cn(
                  "w-4 h-4 text-muted-foreground transition-transform",
                  showDocuments && "rotate-180"
                )}
              />
            </button>
          )}

          {showDocuments && (
            <div className="mt-2 p-3 bg-muted/50 rounded-lg space-y-1.5 max-h-40 overflow-y-auto">
              {documents.map((doc, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 text-xs text-muted-foreground"
                >
                  <FileText className="w-3 h-3" />
                  <span className="truncate">{doc}</span>
                </div>
              ))}
            </div>
          )}

          {/* Reload Button */}
          <Button
            onClick={handleReload}
            variant="outline"
            className="w-full mt-3"
            disabled={isReloading}
          >
            <RefreshCw
              className={cn("w-4 h-4 mr-2", isReloading && "animate-spin")}
            />
            {isReloading ? "Reloading..." : "Reload Documents"}
          </Button>
        </section>

        {/* LLM Provider Selection */}
        {providers.length > 0 && (
          <section>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
              <Cpu className="w-3.5 h-3.5" />
              Language Model
            </h4>
            <div className="space-y-2">
              {providers.map((provider) => (
                <button
                  key={provider}
                  onClick={() => onProviderChange(provider)}
                  className={cn(
                    "w-full px-4 py-2.5 rounded-lg text-sm font-medium transition-all",
                    "flex items-center gap-3",
                    selectedProvider === provider
                      ? "gradient-primary text-primary-foreground shadow-primary"
                      : "bg-muted text-muted-foreground hover:bg-muted/80"
                  )}
                >
                  <div
                    className={cn(
                      "w-2 h-2 rounded-full",
                      selectedProvider === provider
                        ? "bg-primary-foreground"
                        : "bg-muted-foreground/50"
                    )}
                  />
                  {provider}
                </button>
              ))}
            </div>
          </section>
        )}
      </div>
    </aside>
  );
};

const StatusBadge = ({
  success,
  label,
}: {
  success: boolean;
  label: string;
}) => (
  <div
    className={cn(
      "flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium",
      success
        ? "bg-primary text-primary-foreground"
        : "bg-destructive text-destructive-foreground"
    )}
  >
    {success ? (
      <CheckCircle2 className="w-4 h-4" />
    ) : (
      <XCircle className="w-4 h-4" />
    )}
    {label}
  </div>
);
