import React, { useState, useRef, useEffect } from "react";
import { Send, Paperclip, X, FileText } from "lucide-react";
import { useChat } from "@/hooks/use-chat";
import { cn } from "@/lib/utils";
import type { Attachment } from "@/stores/chat-store";

export function ChatInput() {
  const [content, setContent] = useState("");
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const { sendMessage } = useChat();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
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
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const removeAttachment = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSend = () => {
    if (!content.trim() && attachments.length === 0) return;
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

  return (
    <div className="p-3 bg-gray-900/50 backdrop-blur-xl border-t border-gray-100/10">
      {/* Attachment Previews */}
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3 animate-in fade-in slide-in-from-bottom-2">
          {attachments.map((file, i) => (
            <div key={i} className="relative group/item">
              <div className="w-16 h-16 rounded-xl overflow-hidden border border-white/10 bg-gray-800/50 backdrop-blur-md flex items-center justify-center shadow-lg transition-transform hover:scale-105">
                {file.type === "image" ? (
                  <img src={file.url} alt={file.name} className="w-full h-full object-cover" />
                ) : (
                  <div className="flex flex-col items-center gap-1 p-2 text-gray-400">
                    <FileText size={20} />
                    <span className="text-[8px] text-center truncate w-full">{file.name}</span>
                  </div>
                )}
              </div>
              <button
                onClick={() => removeAttachment(i)}
                className="absolute -top-1.5 -right-1.5 bg-red-500 text-white rounded-full p-0.5 shadow-xl opacity-0 group-hover/item:opacity-100 transition-opacity transform hover:scale-110"
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
          placeholder="Ask Architect..."
          rows={1}
          className={cn(
            "w-full bg-gray-800/80 text-gray-100 text-sm rounded-xl py-2.5 pl-10 pr-10 scrollbar-none",
            "border border-gray-700/50 focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/30 transition-all",
            "placeholder:text-gray-500 resize-none max-h-48 shadow-inner"
          )}
        />
        
        {/* Attachment Button */}
        <div className="absolute left-1.5 bottom-1.5 flex items-center">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="p-1.5 text-gray-400 hover:text-gray-100 hover:bg-white/5 rounded-lg transition-all"
            title="Attach files"
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
            disabled={!content.trim() && attachments.length === 0}
            className={cn(
              "p-1.5 rounded-lg transition-all transform hover:scale-105 active:scale-95 shadow-lg",
              (content.trim() || attachments.length > 0)
                ? "bg-blue-600 text-white hover:bg-blue-500 shadow-blue-900/40" 
                : "bg-gray-700/50 text-gray-500 cursor-not-allowed"
            )}
          >
            <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
