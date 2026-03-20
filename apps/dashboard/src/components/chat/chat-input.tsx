import React, { useState, useRef, useEffect } from "react";
import { Send, Paperclip, X, FileText } from "lucide-react";
import { useChat } from "@/hooks/use-chat";
import { cn } from "@/lib/utils";
import type { Attachment } from "@/stores/chat-store";
import { useProjectStore } from "@/stores/project-store";
import { useSocketStore } from "@/stores/socket-store";

export function ChatInput() {
  const [content, setContent] = useState("");
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const { sendMessage } = useChat();
  const activeProjectId = useProjectStore((s) => s.activeProjectId);
  const isConnected = useSocketStore((s) => s.isConnected);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const appendFiles = async (files: File[]) => {
    if (!files.length) return;

    const newAttachments: Attachment[] = await Promise.all(
      files.map(async (file) => {
        return new Promise<Attachment>((resolve) => {
          const reader = new FileReader();
          reader.onloadend = () => {
            resolve({
              type: file.type.startsWith("image/") ? "image" : "file",
              url: reader.result as string,
              name: file.name,
              size: file.size,
            });
          };
          reader.readAsDataURL(file);
        });
      })
    );

    setAttachments((prev) => [...prev, ...newAttachments]);
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    await appendFiles(files);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const removeAttachment = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSend = () => {
    if ((!content.trim() && attachments.length === 0) || !activeProjectId || !isConnected) {
      return;
    }
    sendMessage(content.trim(), attachments);
    setContent("");
    setAttachments([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [content]);

  const canSend = (content.trim() || attachments.length > 0) && activeProjectId && isConnected;

  function getHelperText(): string {
    if (!activeProjectId) {
      return "Open a project to start coordinating with agents.";
    }

    if (!isConnected) {
      return "Chat will resume once the workspace reconnects.";
    }

    return "Press Enter to send, Shift+Enter for a newline, or drop files here.";
  }

  return (
    <div
      className={cn(
        "border-t border-border bg-panel-muted p-3 backdrop-blur-xl transition-colors",
        isDragging && "bg-accent-muted/70",
      )}
      onDragOver={(event) => {
        event.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={(event) => {
        event.preventDefault();
        if (event.currentTarget.contains(event.relatedTarget as Node | null)) {
          return;
        }
        setIsDragging(false);
      }}
      onDrop={(event) => {
        event.preventDefault();
        setIsDragging(false);
        void appendFiles(Array.from(event.dataTransfer.files || []));
      }}
    >
      {/* Attachment Previews */}
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3 animate-in fade-in slide-in-from-bottom-2">
          {attachments.map((file, i) => (
            <div key={i} className="relative group/item">
              <div className="flex h-16 w-16 items-center justify-center overflow-hidden rounded-xl border border-border bg-panel shadow-[var(--theme-shadow-panel)] backdrop-blur-md transition-transform hover:scale-105">
                {file.type === "image" ? (
                  <img src={file.url} alt={file.name} className="w-full h-full object-cover" />
                ) : (
                  <div className="flex flex-col items-center gap-1 p-2 text-muted-foreground">
                    <FileText size={20} />
                    <span className="text-[8px] text-center truncate w-full">{file.name}</span>
                  </div>
                )}
              </div>
              <button
                onClick={() => removeAttachment(i)}
                aria-label={`Remove attachment ${file.name}`}
                className="absolute -top-1.5 -right-1.5 rounded-full bg-danger p-0.5 text-white opacity-0 shadow-xl transition-opacity transform hover:scale-110 group-hover/item:opacity-100"
              >
                <X size={10} />
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="relative group">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={activeProjectId ? "Ask Architect..." : "Select a project to chat"}
          rows={1}
          disabled={!activeProjectId}
          className={cn(
            "max-h-48 w-full resize-none rounded-xl bg-input py-2.5 pl-10 pr-10 text-sm text-foreground scrollbar-none",
            "border border-border transition-all focus:border-border-strong focus:ring-4 focus:ring-ring/60",
            "placeholder:text-muted-foreground shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]",
            !activeProjectId && "cursor-not-allowed opacity-70"
          )}
        />
        
        {/* Attachment Button */}
        <div className="absolute left-1.5 bottom-1.5 flex items-center">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="rounded-lg p-1.5 text-muted-foreground transition-all hover:bg-panel hover:text-foreground"
            title="Attach files"
            aria-label="Attach files"
            disabled={!activeProjectId}
          >
            <Paperclip size={16} />
          </button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            multiple
            className="hidden"
          />
        </div>

        {/* Send Button */}
        <div className="absolute right-1.5 bottom-1.5 flex items-center gap-2">
          <button
            onClick={handleSend}
            disabled={!canSend}
            aria-label="Send chat message"
            className={cn(
              "rounded-lg p-1.5 shadow-lg transition-all transform hover:scale-105 active:scale-95",
              canSend
                ? "bg-accent text-accent-foreground shadow-[var(--theme-shadow-floating)] hover:brightness-105" 
                : "cursor-not-allowed bg-panel text-muted-foreground"
            )}
          >
            <Send size={14} />
          </button>
        </div>
      </div>
      <p className="mt-2 text-[11px] text-muted-foreground">{getHelperText()}</p>
    </div>
  );
}
