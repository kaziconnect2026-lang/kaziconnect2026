import { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { toast } from "sonner";
import {
  ArrowLeft,
  Shield,
  MessageCircle,
  Search,
  FileText,
  Loader2,
  Image as ImageIcon,
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function fmtDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function AdminAttachment({ path, filename, contentType }) {
  const [src, setSrc] = useState(null);
  const [error, setError] = useState(false);
  const url = `${API}/files/chat/${path}`;

  useEffect(() => {
    let cancelled = false;
    let blobUrl = null;
    if (contentType === "application/pdf") return;
    axios
      .get(url, { responseType: "blob" })
      .then((res) => {
        if (cancelled) return;
        blobUrl = URL.createObjectURL(res.data);
        setSrc(blobUrl);
      })
      .catch(() => !cancelled && setError(true));
    return () => {
      cancelled = true;
      if (blobUrl) URL.revokeObjectURL(blobUrl);
    };
  }, [path, contentType, url]);

  if (contentType === "application/pdf") {
    return (
      <button
        onClick={async () => {
          try {
            const res = await axios.get(url, { responseType: "blob" });
            const u = URL.createObjectURL(res.data);
            window.open(u, "_blank");
            setTimeout(() => URL.revokeObjectURL(u), 60000);
          } catch {
            toast.error("Failed to open PDF");
          }
        }}
        className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-background/60 border border-border hover:bg-background text-xs"
      >
        <FileText className="w-4 h-4 text-primary" />
        <span className="truncate max-w-[160px]">{filename || "Document.pdf"}</span>
      </button>
    );
  }

  if (error)
    return (
      <div className="flex items-center gap-2 text-xs text-red-600">
        <ImageIcon className="w-4 h-4" /> Failed to load
      </div>
    );
  if (!src)
    return (
      <div className="w-32 h-32 rounded-lg bg-muted animate-pulse flex items-center justify-center">
        <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
      </div>
    );

  return (
    <img
      src={src}
      alt={filename || ""}
      onClick={() => window.open(src, "_blank")}
      className="rounded-lg max-w-[200px] max-h-[200px] object-cover cursor-pointer border border-border"
    />
  );
}

export default function AdminConversationsPage() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const [conversations, setConversations] = useState([]);
  const [loadingList, setLoadingList] = useState(true);
  const [filter, setFilter] = useState("");
  const [activeConvo, setActiveConvo] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loadingMessages, setLoadingMessages] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await axios.get(`${API}/admin/conversations?limit=300`);
        setConversations(res.data || []);
      } catch (err) {
        toast.error("Failed to load conversations");
      } finally {
        setLoadingList(false);
      }
    };
    load();
  }, []);

  useEffect(() => {
    if (!conversationId) {
      setActiveConvo(null);
      setMessages([]);
      return;
    }
    const fetchData = async () => {
      setLoadingMessages(true);
      try {
        const [convRes, msgRes] = await Promise.all([
          axios.get(`${API}/conversations/${conversationId}`),
          axios.get(`${API}/conversations/${conversationId}/messages?limit=500`),
        ]);
        setActiveConvo(convRes.data);
        setMessages(msgRes.data || []);
      } catch (err) {
        toast.error("Failed to load conversation");
      } finally {
        setLoadingMessages(false);
      }
    };
    fetchData();
  }, [conversationId]);

  const filtered = conversations.filter((c) => {
    if (!filter) return true;
    const q = filter.toLowerCase();
    return (
      c.client?.name?.toLowerCase().includes(q) ||
      c.professional?.name?.toLowerCase().includes(q) ||
      c.client?.display_id?.toLowerCase().includes(q) ||
      c.professional?.display_id?.toLowerCase().includes(q) ||
      c.last_message_preview?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="min-h-screen bg-background" data-testid="admin-conversations-page">
      <header className="border-b border-border sticky top-0 z-30 bg-background/95 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-3">
          <button
            onClick={() => navigate("/admin")}
            className="p-2 rounded-full hover:bg-muted"
            data-testid="admin-back-btn"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-red-600" />
            <h1 className="font-semibold text-lg">Chat Moderation</h1>
            <Badge variant="outline" className="ml-2 text-xs">
              {conversations.length} total
            </Badge>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 grid lg:grid-cols-[360px_1fr] gap-6">
        {/* Conversation list */}
        <Card className="overflow-hidden self-start">
          <div className="p-3 border-b border-border">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search by name, ID, message..."
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="pl-9 h-10"
                data-testid="admin-convo-search"
              />
            </div>
          </div>
          <div className="max-h-[70vh] overflow-y-auto divide-y divide-border">
            {loadingList ? (
              <p className="p-6 text-center text-sm text-muted-foreground">Loading...</p>
            ) : filtered.length === 0 ? (
              <p className="p-8 text-center text-sm text-muted-foreground">
                No conversations found.
              </p>
            ) : (
              filtered.map((c) => (
                <Link
                  key={c.id}
                  to={`/admin/conversations/${c.id}`}
                  className={`block px-4 py-3 hover:bg-muted/50 transition-colors ${
                    c.id === conversationId ? "bg-primary/5 border-l-2 border-primary" : ""
                  }`}
                  data-testid={`admin-convo-row-${c.id}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium truncate">
                      {c.client?.name || "?"} ↔ {c.professional?.name || "?"}
                    </p>
                    <span className="text-[10px] text-muted-foreground shrink-0">
                      {fmtDate(c.last_message_at)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-2 mt-1">
                    <p className="text-xs text-muted-foreground truncate">
                      {c.last_message_preview || "No messages yet"}
                    </p>
                    <Badge variant="outline" className="text-[10px] shrink-0">
                      {c.message_count || 0}
                    </Badge>
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-1 truncate">
                    {c.client?.display_id} · {c.professional?.display_id}
                  </p>
                </Link>
              ))
            )}
          </div>
        </Card>

        {/* Conversation detail */}
        <Card className="overflow-hidden min-h-[70vh] flex flex-col">
          {!conversationId ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-10">
              <MessageCircle className="w-10 h-10 text-muted-foreground mb-3" />
              <p className="font-medium">Select a conversation</p>
              <p className="text-sm text-muted-foreground mt-1">
                Choose a conversation from the list to view all messages and attachments for
                dispute resolution.
              </p>
            </div>
          ) : loadingMessages ? (
            <div className="flex-1 flex items-center justify-center">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              <div className="px-5 py-4 border-b border-border bg-muted/30">
                <p className="text-sm text-muted-foreground">Conversation</p>
                <p className="font-semibold">
                  Client: <span className="text-foreground">{activeConvo?.client_id}</span> ·
                  Pro: <span className="text-foreground">{activeConvo?.professional_id}</span>
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Started {fmtDate(activeConvo?.created_at)} · {messages.length} messages
                </p>
              </div>
              <div className="flex-1 overflow-y-auto p-5 space-y-3 bg-muted/20">
                {messages.length === 0 ? (
                  <p className="text-center text-sm text-muted-foreground py-10">
                    No messages in this conversation.
                  </p>
                ) : (
                  messages.map((m) => (
                    <div
                      key={m.id}
                      className="bg-card border border-border rounded-xl p-3"
                      data-testid={`admin-message-${m.id}`}
                    >
                      <div className="flex items-center justify-between mb-1.5 gap-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <Badge
                            variant="outline"
                            className={`text-[10px] ${
                              m.sender_role === "client"
                                ? "border-blue-300 text-blue-700"
                                : "border-emerald-300 text-emerald-700"
                            }`}
                          >
                            {m.sender_role}
                          </Badge>
                          <p className="text-sm font-medium truncate">
                            {m.sender_name || "Unknown"}
                          </p>
                        </div>
                        <span className="text-[10px] text-muted-foreground shrink-0">
                          {fmtDate(m.created_at)}
                        </span>
                      </div>
                      {m.content && (
                        <p className="text-sm whitespace-pre-wrap break-words">{m.content}</p>
                      )}
                      {m.attachments && m.attachments.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {m.attachments.map((a) => (
                            <AdminAttachment
                              key={a.path}
                              path={a.path}
                              filename={a.filename}
                              contentType={a.content_type}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
