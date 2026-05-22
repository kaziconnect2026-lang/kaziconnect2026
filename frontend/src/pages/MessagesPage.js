import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { Card } from "../components/ui/card";
import { ArrowLeft, MessageCircle, Search } from "lucide-react";
import { Input } from "../components/ui/input";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function relativeTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return d.toLocaleDateString();
}

export default function MessagesPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  const fetchConvos = async () => {
    try {
      const res = await axios.get(`${API}/conversations`);
      setConversations(res.data || []);
    } catch (err) {
      toast.error("Failed to load conversations");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConvos();
    const t = setInterval(fetchConvos, 5000);
    return () => clearInterval(t);
  }, []);

  const filtered = conversations.filter((c) => {
    const name = (c.other_user?.name || "").toLowerCase();
    return !filter || name.includes(filter.toLowerCase());
  });

  const dashboardHref = user?.role === "client" ? "/client" : "/professional";

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border sticky top-0 z-30 bg-background/95 backdrop-blur">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-3">
          <button
            onClick={() => navigate(dashboardHref)}
            className="p-2 rounded-full hover:bg-muted"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex-1">
            <h1 className="text-xl font-semibold tracking-tight">Messages</h1>
            <p className="text-xs text-muted-foreground">Chat with {user?.role === "client" ? "professionals" : "clients"}</p>
          </div>
          <MessageCircle className="w-5 h-5 text-muted-foreground" />
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-6 space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search conversations..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="pl-9 h-11 rounded-xl"
            data-testid="convo-search"
          />
        </div>

        {loading ? (
          <p className="text-center text-sm text-muted-foreground py-12">Loading...</p>
        ) : filtered.length === 0 ? (
          <Card className="p-10 text-center border-dashed">
            <MessageCircle className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
            <p className="text-sm font-medium">No conversations yet</p>
            <p className="text-xs text-muted-foreground mt-1">
              {user?.role === "client"
                ? "Start a chat from a professional's profile."
                : "Conversations will appear when a client messages you."}
            </p>
            {user?.role === "client" && (
              <Link
                to="/search"
                className="inline-block mt-4 text-sm text-primary font-medium hover:underline"
                data-testid="browse-pros-link"
              >
                Browse professionals →
              </Link>
            )}
          </Card>
        ) : (
          <div className="divide-y divide-border rounded-2xl border border-border overflow-hidden bg-card">
            {filtered.map((c) => (
              <Link
                key={c.id}
                to={`/messages/${c.id}`}
                className="flex items-center gap-3 px-4 py-3 hover:bg-muted/50 transition-colors"
                data-testid={`convo-row-${c.id}`}
              >
                <div className="w-11 h-11 rounded-full bg-primary/10 flex items-center justify-center font-semibold text-primary shrink-0 overflow-hidden">
                  {c.other_user?.profile_photo ? (
                    <img src={c.other_user.profile_photo} alt="" className="w-full h-full object-cover" />
                  ) : (
                    (c.other_user?.name || "?").charAt(0).toUpperCase()
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-medium truncate text-sm">{c.other_user?.name || "Unknown"}</p>
                    <span className="text-xs text-muted-foreground shrink-0">{relativeTime(c.last_message_at)}</span>
                  </div>
                  <div className="flex items-center justify-between gap-2 mt-0.5">
                    <p className="text-sm text-muted-foreground truncate">
                      {c.last_message_preview || "No messages yet"}
                    </p>
                    {c.unread > 0 && (
                      <span
                        className="bg-primary text-primary-foreground text-xs font-medium rounded-full min-w-[20px] h-5 px-1.5 inline-flex items-center justify-center"
                        data-testid={`unread-badge-${c.id}`}
                      >
                        {c.unread}
                      </span>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
