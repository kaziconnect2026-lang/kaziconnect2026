import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { ArrowLeft, Send, Paperclip, X, FileText, Loader2 } from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const POLL_INTERVAL = 3000;
const MAX_ATTACHMENTS = 6;
const MAX_SIZE = 5 * 1024 * 1024;
const ALLOWED = ["image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf"];

function formatTime(iso) {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function authedAttachmentUrl(path) {
  // Backend serves at /api/files/chat/{path}. Since axios default header is set globally,
  // we use a small fetch + blob URL so <img> tags can show auth-required content.
  return `${API}/files/chat/${path}`;
}

function AttachmentImage({ path, filename, contentType }) {
  const [src, setSrc] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let blobUrl = null;
    axios
      .get(authedAttachmentUrl(path), { responseType: "blob" })
      .then((res) => {
        if (cancelled) return;
        blobUrl = URL.createObjectURL(res.data);
        setSrc(blobUrl);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
      if (blobUrl) URL.revokeObjectURL(blobUrl);
    };
  }, [path]);

  if (contentType === "application/pdf") {
    return (
      <a
        href="#"
        onClick={async (e) => {
          e.preventDefault();
          try {
            const res = await axios.get(authedAttachmentUrl(path), { responseType: "blob" });
            const url = URL.createObjectURL(res.data);
            window.open(url, "_blank");
            setTimeout(() => URL.revokeObjectURL(url), 60000);
          } catch {
            toast.error("Failed to open PDF");
          }
        }}
        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-background/60 border border-border hover:bg-background"
        data-testid="pdf-attachment"
      >
        <FileText className="w-4 h-4 text-primary" />
        <span className="text-sm truncate max-w-[200px]">{filename || "Document.pdf"}</span>
      </a>
    );
  }

  if (error) return <div className="text-xs text-red-600">Failed to load image</div>;
  if (!src)
    return (
      <div className="w-40 h-40 rounded-lg bg-muted animate-pulse flex items-center justify-center">
        <Loader2 className="w-5 h-5 text-muted-foreground animate-spin" />
      </div>
    );
  return (
    <img
      src={src}
      alt={filename || ""}
      className="rounded-lg max-w-[260px] max-h-[260px] object-cover cursor-pointer"
      onClick={() => window.open(src, "_blank")}
      data-testid="image-attachment"
    />
  );
}

export default function ChatThreadPage() {
  const { conversationId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [convo, setConvo] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [pendingFiles, setPendingFiles] = useState([]); // [{file, uploading, path?, content_type?}]
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const fetchConvo = async () => {
    try {
      const res = await axios.get(`${API}/conversations/${conversationId}`);
      setConvo(res.data);
    } catch (err) {
      toast.error("Conversation not found");
      navigate("/messages");
    }
  };

  const fetchMessages = async () => {
    try {
      const res = await axios.get(`${API}/conversations/${conversationId}/messages`);
      setMessages(res.data || []);
    } catch (err) {
      // silent on polling errors
    }
  };

  useEffect(() => {
    fetchConvo();
    fetchMessages();
    const t = setInterval(fetchMessages, POLL_INTERVAL);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  const handlePickFiles = (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    const available = MAX_ATTACHMENTS - pendingFiles.length;
    if (available <= 0) {
      toast.error(`Maximum ${MAX_ATTACHMENTS} attachments per message`);
      return;
    }
    const toAdd = files.slice(0, available);
    for (const f of toAdd) {
      if (!ALLOWED.includes(f.type)) {
        toast.error(`${f.name}: only images and PDFs are allowed`);
        continue;
      }
      if (f.size > MAX_SIZE) {
        toast.error(`${f.name} is larger than 5 MB`);
        continue;
      }
      uploadFile(f);
    }
    e.target.value = "";
  };

  const uploadFile = async (file) => {
    const tempId = `${file.name}-${Date.now()}-${Math.random()}`;
    setPendingFiles((prev) => [...prev, { tempId, file, uploading: true }]);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await axios.post(`${API}/chat/attachments`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setPendingFiles((prev) =>
        prev.map((p) =>
          p.tempId === tempId
            ? { ...p, uploading: false, path: res.data.path, content_type: res.data.content_type }
            : p
        )
      );
    } catch (err) {
      toast.error(err.response?.data?.detail || `Failed to upload ${file.name}`);
      setPendingFiles((prev) => prev.filter((p) => p.tempId !== tempId));
    }
  };

  const removePending = (tempId) => {
    setPendingFiles((prev) => prev.filter((p) => p.tempId !== tempId));
  };

  const handleSend = async (e) => {
    e?.preventDefault?.();
    const trimmed = input.trim();
    const ready = pendingFiles.filter((p) => !p.uploading && p.path);
    if (!trimmed && ready.length === 0) return;
    if (pendingFiles.some((p) => p.uploading)) {
      toast.message("Waiting for attachments to upload...");
      return;
    }
    setSending(true);
    try {
      await axios.post(`${API}/conversations/${conversationId}/messages`, {
        content: trimmed,
        attachment_paths: ready.map((p) => p.path),
      });
      setInput("");
      setPendingFiles([]);
      await fetchMessages();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to send");
    } finally {
      setSending(false);
    }
  };

  if (!convo) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-6 h-6 text-muted-foreground animate-spin" />
      </div>
    );
  }

  const other = convo.other_user || {};

  return (
    <div className="min-h-screen bg-muted/30 flex flex-col">
      {/* Header */}
      <header className="border-b border-border bg-background/95 backdrop-blur sticky top-0 z-30">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-3">
          <button
            onClick={() => navigate("/messages")}
            className="p-2 rounded-full hover:bg-muted"
            data-testid="back-to-list-btn"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center font-semibold text-primary shrink-0 overflow-hidden">
            {other.profile_photo ? (
              <img src={other.profile_photo} alt="" className="w-full h-full object-cover" />
            ) : (
              (other.name || "?").charAt(0).toUpperCase()
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-sm truncate" data-testid="chat-other-name">{other.name || "Unknown"}</p>
            <p className="text-xs text-muted-foreground truncate">
              {other.role === "professional" ? "Service Professional" : "Client"}
              {other.location ? ` · ${other.location}` : ""}
            </p>
          </div>
        </div>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6 space-y-3">
          {messages.length === 0 ? (
            <div className="text-center py-12 text-sm text-muted-foreground">
              No messages yet. Say hello!
            </div>
          ) : (
            messages.map((m) => {
              const mine = m.sender_id === user.id;
              return (
                <div
                  key={m.id}
                  className={`flex ${mine ? "justify-end" : "justify-start"}`}
                  data-testid={`message-${m.id}`}
                >
                  <div
                    className={`max-w-[78%] rounded-2xl px-4 py-2.5 ${
                      mine
                        ? "bg-primary text-primary-foreground rounded-br-md"
                        : "bg-card border border-border rounded-bl-md"
                    }`}
                  >
                    {m.content && (
                      <p className="text-sm whitespace-pre-wrap break-words">{m.content}</p>
                    )}
                    {m.attachments && m.attachments.length > 0 && (
                      <div className={`${m.content ? "mt-2" : ""} space-y-2`}>
                        {m.attachments.map((a) => (
                          <AttachmentImage
                            key={a.path}
                            path={a.path}
                            filename={a.filename}
                            contentType={a.content_type}
                          />
                        ))}
                      </div>
                    )}
                    <p
                      className={`text-[10px] mt-1 ${
                        mine ? "text-primary-foreground/70" : "text-muted-foreground"
                      } text-right`}
                    >
                      {formatTime(m.created_at)}
                    </p>
                  </div>
                </div>
              );
            })
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Composer */}
      <footer className="border-t border-border bg-background sticky bottom-0">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-3">
          {pendingFiles.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-2">
              {pendingFiles.map((p) => (
                <div
                  key={p.tempId}
                  className="relative inline-flex items-center gap-2 bg-muted rounded-lg px-2.5 py-1.5 text-xs"
                  data-testid="pending-attachment"
                >
                  {p.uploading ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : p.content_type === "application/pdf" ? (
                    <FileText className="w-3.5 h-3.5 text-primary" />
                  ) : null}
                  <span className="max-w-[140px] truncate">{p.file.name}</span>
                  <button
                    type="button"
                    onClick={() => removePending(p.tempId)}
                    className="hover:bg-background rounded-full p-0.5"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
          <form onSubmit={handleSend} className="flex items-end gap-2">
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/jpeg,image/png,image/webp,image/gif,application/pdf"
              onChange={handlePickFiles}
              className="hidden"
              data-testid="file-input"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="p-3 rounded-full hover:bg-muted text-muted-foreground"
              data-testid="attach-btn"
              aria-label="Attach file"
            >
              <Paperclip className="w-5 h-5" />
            </button>
            <Input
              placeholder="Type a message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="flex-1 h-11 rounded-2xl"
              maxLength={4000}
              data-testid="message-input"
            />
            <Button
              type="submit"
              disabled={sending || (!input.trim() && pendingFiles.filter((p) => p.path).length === 0)}
              className="h-11 w-11 rounded-full p-0"
              data-testid="send-btn"
            >
              {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </Button>
          </form>
        </div>
      </footer>
    </div>
  );
}
