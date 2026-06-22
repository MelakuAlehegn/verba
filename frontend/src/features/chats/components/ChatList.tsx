import { MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import { NavLink, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { useChats, useDeleteChat, useRenameChat } from "@/features/chats/hooks";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import {
  SidebarInput,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { Skeleton } from "@/components/ui/skeleton";
import type { Chat } from "@/lib/api/types";

export function ChatList() {
  const { data: chats, isLoading } = useChats();
  const { chatId } = useParams();
  const navigate = useNavigate();
  const { isMobile, setOpenMobile } = useSidebar();
  const renameChat = useRenameChat();
  const deleteChat = useDeleteChat();

  const [query, setQuery] = useState("");
  const [renaming, setRenaming] = useState<Chat | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [deleting, setDeleting] = useState<Chat | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-1 px-2">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-7 w-full" />
        ))}
      </div>
    );
  }

  const filtered = (chats ?? []).filter((chat) =>
    chat.title.toLowerCase().includes(query.trim().toLowerCase()),
  );

  const submitRename = () => {
    if (!renaming) return;
    const title = renameValue.trim();
    if (title && title !== renaming.title) {
      renameChat.mutate({ id: renaming.id, title });
    }
    setRenaming(null);
  };

  const confirmDelete = () => {
    if (!deleting) return;
    const wasActive = deleting.id === chatId;
    deleteChat.mutate(deleting.id, {
      onSuccess: () => {
        toast(`Deleted “${deleting.title}”.`);
        if (wasActive) navigate("/app");
      },
      onError: () => toast.error("Couldn't delete that chat."),
    });
    setDeleting(null);
  };

  return (
    <>
      {(chats?.length ?? 0) > 6 ? (
        <div className="px-2 pb-1">
          <SidebarInput
            placeholder="Search chats"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
      ) : null}

      {filtered.length === 0 ? (
        <p className="px-2 py-1.5 text-xs text-muted-foreground">
          {query ? "No chats match." : "No chats yet. Start by asking a question."}
        </p>
      ) : (
        <SidebarMenu>
          {filtered.map((chat) => (
            <SidebarMenuItem key={chat.id}>
              <SidebarMenuButton asChild isActive={chat.id === chatId} tooltip={chat.title}>
                <NavLink
                  to={`/app/chats/${chat.id}`}
                  onClick={() => isMobile && setOpenMobile(false)}
                >
                  <span className="truncate">{chat.title}</span>
                </NavLink>
              </SidebarMenuButton>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <SidebarMenuAction showOnHover aria-label="Chat options">
                    <MoreHorizontal />
                  </SidebarMenuAction>
                </DropdownMenuTrigger>
                <DropdownMenuContent side="right" align="start">
                  <DropdownMenuItem
                    onSelect={() => {
                      setRenaming(chat);
                      setRenameValue(chat.title);
                    }}
                  >
                    <Pencil className="h-4 w-4" />
                    Rename
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    className="text-destructive focus:text-destructive"
                    onSelect={() => setDeleting(chat)}
                  >
                    <Trash2 className="h-4 w-4" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      )}

      <Dialog open={renaming !== null} onOpenChange={(open) => !open && setRenaming(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename chat</DialogTitle>
          </DialogHeader>
          <Input
            value={renameValue}
            onChange={(event) => setRenameValue(event.target.value)}
            onKeyDown={(event) => event.key === "Enter" && submitRename()}
            autoFocus
          />
          <DialogFooter>
            <Button variant="ghost" onClick={() => setRenaming(null)}>
              Cancel
            </Button>
            <Button onClick={submitRename}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleting !== null} onOpenChange={(open) => !open && setDeleting(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this chat?</AlertDialogTitle>
            <AlertDialogDescription>
              “{deleting?.title}” and its messages will be permanently removed.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
