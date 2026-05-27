import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Textarea } from "../components/ui/textarea";
import { toast } from "sonner";
import {
  ArrowLeft, ShieldCheck, Loader2, CheckCircle2, XCircle,
  User as UserIcon, Phone, Mail, MapPin,
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AuthedImage({ url, className }) {
  const [src, setSrc] = useState(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    if (!url) return;
    let blobUrl = null;
    let cancelled = false;
    const full = url.startsWith("http") ? url : `${BACKEND_URL}${url}`;
    axios.get(full, { responseType: "blob" })
      .then((r) => {
        if (cancelled) return;
        blobUrl = URL.createObjectURL(r.data);
        setSrc(blobUrl);
      })
      .catch(() => !cancelled && setError(true));
    return () => {
      cancelled = true;
      if (blobUrl) URL.revokeObjectURL(blobUrl);
    };
  }, [url]);

  if (error) return <div className={`${className} bg-red-50 text-red-700 text-xs flex items-center justify-center`}>Failed to load</div>;
  if (!src) return <div className={`${className} bg-muted animate-pulse flex items-center justify-center`}><Loader2 className="w-5 h-5 animate-spin text-muted-foreground" /></div>;
  return <img src={src} alt="ID" className={className} onClick={() => window.open(src, "_blank")} />;
}

export default function AdminKycPage() {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState(null);
  const [activeLoading, setActiveLoading] = useState(false);
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchPending();
  }, []);

  useEffect(() => {
    if (!userId) {
      setActive(null);
      return;
    }
    fetchActive(userId);
  }, [userId]);

  const fetchPending = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/admin/kyc/pending`);
      setPending(res.data || []);
    } catch (err) {
      toast.error("Failed to load pending KYC submissions");
    } finally {
      setLoading(false);
    }
  };

  const fetchActive = async (id) => {
    setActiveLoading(true);
    try {
      const res = await axios.get(`${API}/admin/kyc/${id}`);
      setActive(res.data);
      setNotes("");
    } catch (err) {
      toast.error("Failed to load user KYC");
      setActive(null);
    } finally {
      setActiveLoading(false);
    }
  };

  const decide = async (approved) => {
    if (!active?.user) return;
    setSubmitting(true);
    try {
      await axios.post(`${API}/admin/kyc/${active.user.id}/verify`, {
        approved,
        notes: notes.trim() || null,
      });
      toast.success(approved ? "Verified ✓" : "Rejected — user will be notified");
      // Refresh list and clear detail
      setPending((prev) => prev.filter((p) => p.id !== active.user.id));
      navigate("/admin/kyc");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Action failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background" data-testid="admin-kyc-page">
      <header className="sticky top-0 z-30 border-b border-border bg-background/95 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-3">
          <button onClick={() => navigate("/admin")} className="p-2 rounded-full hover:bg-muted" data-testid="kyc-back-btn">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <ShieldCheck className="w-5 h-5 text-primary" />
          <h1 className="font-semibold text-lg">KYC Review</h1>
          <Badge variant="outline" className="ml-2 text-xs" data-testid="kyc-pending-count">
            {pending.length} pending
          </Badge>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 grid lg:grid-cols-[340px_1fr] gap-6">
        {/* Pending list */}
        <Card className="self-start overflow-hidden">
          <div className="px-4 py-3 border-b border-border bg-muted/30">
            <p className="font-medium text-sm">Awaiting review</p>
          </div>
          <div className="max-h-[70vh] overflow-y-auto divide-y divide-border">
            {loading ? (
              <p className="p-6 text-center text-sm text-muted-foreground">Loading…</p>
            ) : pending.length === 0 ? (
              <p className="p-8 text-center text-sm text-muted-foreground">
                No pending KYC submissions.
              </p>
            ) : (
              pending.map((u) => (
                <button
                  key={u.id}
                  onClick={() => navigate(`/admin/kyc/${u.id}`)}
                  className={`block w-full text-left px-4 py-3 hover:bg-muted/40 transition-colors ${
                    u.id === userId ? "bg-primary/5 border-l-2 border-primary" : ""
                  }`}
                  data-testid={`kyc-pending-row-${u.id}`}
                >
                  <p className="text-sm font-medium truncate">{u.name}</p>
                  <p className="text-xs text-muted-foreground truncate">
                    {u.email} · {u.role}
                  </p>
                  <p className="text-[10px] text-muted-foreground mt-0.5">
                    Uploaded {u.id_uploaded_at ? new Date(u.id_uploaded_at).toLocaleString() : "—"}
                  </p>
                </button>
              ))
            )}
          </div>
        </Card>

        {/* Detail */}
        <Card className="overflow-hidden min-h-[70vh]">
          {!userId ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-10 h-full">
              <ShieldCheck className="w-10 h-10 text-muted-foreground mb-3" />
              <p className="font-medium">Select a user</p>
              <p className="text-sm text-muted-foreground mt-1">
                Pick someone on the left to review their ID and approve or reject.
              </p>
            </div>
          ) : activeLoading || !active ? (
            <div className="flex items-center justify-center h-full p-10">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <CardContent className="p-5 sm:p-6 space-y-5">
              {/* User card */}
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <UserIcon className="w-6 h-6 text-primary" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-heading font-semibold text-lg truncate" data-testid="kyc-user-name">{active.user.name}</p>
                  <p className="text-xs text-muted-foreground capitalize">
                    {active.user.role} · {active.user.display_id}
                  </p>
                  <div className="text-xs text-muted-foreground mt-1 flex flex-wrap gap-x-3 gap-y-0.5">
                    <span className="inline-flex items-center gap-1"><Mail className="w-3 h-3" />{active.user.email}</span>
                    {active.user.phone && <span className="inline-flex items-center gap-1"><Phone className="w-3 h-3" />{active.user.phone}</span>}
                    {active.user.location && <span className="inline-flex items-center gap-1"><MapPin className="w-3 h-3" />{active.user.location}</span>}
                  </div>
                </div>
                {active.user.id_verified ? (
                  <Badge className="bg-green-100 text-green-800 border-0">Verified</Badge>
                ) : active.user.id_verification_status === "rejected" ? (
                  <Badge className="bg-red-100 text-red-800 border-0">Rejected</Badge>
                ) : (
                  <Badge className="bg-amber-100 text-amber-900 border-0">Pending</Badge>
                )}
              </div>

              {/* ID images */}
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <p className="text-xs font-medium text-muted-foreground">Front of ID</p>
                  <AuthedImage
                    url={active.id_front_url}
                    className="w-full aspect-[16/10] rounded-xl object-cover border border-border cursor-zoom-in"
                  />
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-medium text-muted-foreground">Back of ID</p>
                  <AuthedImage
                    url={active.id_back_url}
                    className="w-full aspect-[16/10] rounded-xl object-cover border border-border cursor-zoom-in"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-sm font-medium">Internal notes (optional)</p>
                <Textarea
                  rows={3}
                  placeholder="e.g. Front photo blurry — please re-upload"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="resize-none"
                  data-testid="kyc-notes"
                />
              </div>

              <div className="flex flex-wrap gap-3 pt-2 border-t border-border">
                <Button
                  variant="outline"
                  className="rounded-xl h-11 border-red-200 text-red-700 hover:bg-red-50"
                  onClick={() => decide(false)}
                  disabled={submitting}
                  data-testid="kyc-reject-btn"
                >
                  <XCircle className="w-4 h-4 mr-1.5" />
                  Reject
                </Button>
                <Button
                  className="rounded-xl h-11 bg-green-600 hover:bg-green-700"
                  onClick={() => decide(true)}
                  disabled={submitting}
                  data-testid="kyc-approve-btn"
                >
                  <CheckCircle2 className="w-4 h-4 mr-1.5" />
                  Approve & Verify
                </Button>
              </div>
            </CardContent>
          )}
        </Card>
      </div>
    </div>
  );
}
