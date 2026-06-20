import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Card, CardContent } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";
import { toast } from "sonner";
import {
  ArrowLeft, ShieldCheck, Search, Loader2, Download, RefreshCw,
  Briefcase, UserCheck, CheckCircle2, Clock, XCircle, TrendingUp,
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const PAGE_SIZE = 100;

const fmtKsh = (n) => `KSh ${Number(n || 0).toLocaleString()}`;
const fmtDate = (iso) => (iso ? new Date(iso).toLocaleString([], {
  month: "short", day: "numeric", year: "2-digit", hour: "2-digit", minute: "2-digit",
}) : "—");

function StatusBadge({ status }) {
  if (status === "completed") return (
    <Badge className="bg-green-100 text-green-800 border-0 gap-1">
      <CheckCircle2 className="w-3 h-3" />Paid
    </Badge>
  );
  if (status === "pending") return (
    <Badge className="bg-amber-100 text-amber-900 border-0 gap-1">
      <Clock className="w-3 h-3" />Awaiting PIN
    </Badge>
  );
  if (status === "failed") return (
    <Badge className="bg-red-100 text-red-800 border-0 gap-1">
      <XCircle className="w-3 h-3" />Failed
    </Badge>
  );
  return <Badge variant="outline">{status}</Badge>;
}

export default function AdminRegistrationPaymentsPage() {
  const navigate = useNavigate();
  const [data, setData] = useState({ registrations: [], summary: null, pagination: null, fees: null });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    role: "all", status: "all", q: "", date_from: "", date_to: "", page: 0,
  });

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    if (filters.role !== "all") params.set("role", filters.role);
    if (filters.status !== "all") params.set("status", filters.status);
    if (filters.q.trim()) params.set("q", filters.q.trim());
    if (filters.date_from) params.set("date_from", filters.date_from);
    if (filters.date_to) params.set("date_to", filters.date_to);
    params.set("limit", String(PAGE_SIZE));
    params.set("skip", String(filters.page * PAGE_SIZE));
    return params.toString();
  }, [filters]);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await axios.get(`${API}/admin/registration-payments?${queryString}`);
        setData(res.data);
      } catch (err) {
        toast.error(err.response?.data?.detail || "Failed to load registration payments");
      } finally {
        setLoading(false);
      }
    };
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
  }, [queryString]);

  const update = (patch) => setFilters((p) => ({ ...p, ...patch, page: 0 }));

  const exportCsv = () => {
    if (!data.registrations || data.registrations.length === 0) {
      toast.error("Nothing to export");
      return;
    }
    const headers = [
      "Date", "Role", "Status", "Amount (KSh)", "M-Pesa Receipt", "Reference",
      "Name", "Email", "Phone", "User Display ID",
    ];
    const rows = data.registrations.map((r) => [
      fmtDate(r.created_at),
      r.role,
      r.status,
      Number(r.amount || 0).toFixed(2),
      r.mpesa_receipt || "",
      r.reference || "",
      r.name || "",
      r.email || "",
      r.phone || "",
      r.user_display_id || "",
    ]);
    const csv = [headers, ...rows]
      .map((row) => row.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(","))
      .join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `kazi-links-registrations-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
    toast.success(`Exported ${rows.length} rows`);
  };

  const s = data.summary || {};
  const fees = data.fees || { client_verification: 20, professional_registration: 2000 };
  const totalPages = data.pagination ? Math.ceil(data.pagination.total / PAGE_SIZE) : 0;
  const currentPage = filters.page + 1;

  return (
    <div className="min-h-screen bg-background" data-testid="admin-registration-payments-page">
      <header className="sticky top-0 z-30 border-b border-border bg-background/95 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-3">
          <button onClick={() => navigate("/admin")} className="p-2 rounded-full hover:bg-muted" data-testid="back-btn">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <ShieldCheck className="w-5 h-5 text-primary" />
          <h1 className="font-semibold text-lg">Registration Payments</h1>
          {data.pagination && (
            <Badge variant="outline" className="ml-2 text-xs">{data.pagination.total} total</Badge>
          )}
          <div className="ml-auto flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setFilters((p) => ({ ...p }))}
              className="gap-2 rounded-lg"
              data-testid="refresh-btn"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button onClick={exportCsv} size="sm" className="gap-2 rounded-lg" data-testid="export-csv-btn">
              <Download className="w-4 h-4" /> Export CSV
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Fee summary banner */}
        <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 text-sm">
          <p className="font-medium mb-1 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-primary" />
            Current registration fees
          </p>
          <p className="text-muted-foreground">
            Clients pay <span className="font-semibold text-foreground">{fmtKsh(fees.client_verification)}</span>{" "}
            (M-Pesa account verification). Professionals pay{" "}
            <span className="font-semibold text-foreground">{fmtKsh(fees.professional_registration)}</span>{" "}
            (joining fee). Accounts are only created after M-Pesa confirms the payment.
          </p>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <SummaryCard
            label="Client Verifications"
            value={fmtKsh(s.client_completed?.total)}
            sub={`${s.client_completed?.count || 0} paid · ${(s.client_pending?.count || 0) + (s.client_failed?.count || 0)} pending/failed`}
            icon={<UserCheck className="w-5 h-5" />}
            tone="blue"
            testId="summary-client"
          />
          <SummaryCard
            label="Pro Registrations"
            value={fmtKsh(s.professional_completed?.total)}
            sub={`${s.professional_completed?.count || 0} paid · ${(s.professional_pending?.count || 0) + (s.professional_failed?.count || 0)} pending/failed`}
            icon={<Briefcase className="w-5 h-5" />}
            tone="amber"
            testId="summary-pro"
          />
          <SummaryCard
            label="Total Revenue"
            value={fmtKsh(s.total_revenue)}
            sub="Confirmed payments only"
            icon={<TrendingUp className="w-5 h-5" />}
            tone="green"
            testId="summary-revenue"
          />
          <SummaryCard
            label="All Attempts"
            value={String(s.total_transactions || 0)}
            sub="Including pending & failed"
            icon={<ShieldCheck className="w-5 h-5" />}
            tone="primary"
            testId="summary-attempts"
          />
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="p-4 sm:p-5">
            <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3">
              <div className="relative lg:col-span-2">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search by name, email, phone, receipt…"
                  value={filters.q}
                  onChange={(e) => update({ q: e.target.value })}
                  className="pl-9 h-10"
                  data-testid="reg-search"
                />
              </div>
              <Select value={filters.role} onValueChange={(v) => update({ role: v })}>
                <SelectTrigger className="h-10" data-testid="reg-role-filter"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All roles</SelectItem>
                  <SelectItem value="client">Clients</SelectItem>
                  <SelectItem value="professional">Professionals</SelectItem>
                </SelectContent>
              </Select>
              <Select value={filters.status} onValueChange={(v) => update({ status: v })}>
                <SelectTrigger className="h-10" data-testid="reg-status-filter"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All statuses</SelectItem>
                  <SelectItem value="completed">Paid</SelectItem>
                  <SelectItem value="pending">Awaiting PIN</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                </SelectContent>
              </Select>
              <div className="flex items-center gap-2">
                <Input
                  type="date" value={filters.date_from}
                  onChange={(e) => update({ date_from: e.target.value })}
                  className="h-10" data-testid="reg-date-from" aria-label="From date"
                />
                <Input
                  type="date" value={filters.date_to}
                  onChange={(e) => update({ date_to: e.target.value })}
                  className="h-10" data-testid="reg-date-to" aria-label="To date"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Table */}
        <Card className="overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : data.registrations.length === 0 ? (
            <div className="text-center py-16 text-muted-foreground" data-testid="reg-empty">
              <ShieldCheck className="w-12 h-12 mx-auto mb-3 opacity-40" />
              <p className="text-sm">No registration payments match your filters.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="reg-table">
                <thead className="bg-muted/40 border-b border-border">
                  <tr className="text-left text-xs uppercase tracking-wide text-muted-foreground">
                    <th className="px-4 py-3 font-medium">Date</th>
                    <th className="px-4 py-3 font-medium">Role</th>
                    <th className="px-4 py-3 font-medium">Name / Email</th>
                    <th className="px-4 py-3 font-medium">Phone</th>
                    <th className="px-4 py-3 font-medium text-right">Amount</th>
                    <th className="px-4 py-3 font-medium">M-Pesa Receipt</th>
                    <th className="px-4 py-3 font-medium">Reference</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.registrations.map((r) => (
                    <tr
                      key={r.id}
                      className="border-b border-border last:border-0 hover:bg-muted/20 transition-colors"
                      data-testid={`reg-row-${r.id}`}
                    >
                      <td className="px-4 py-3 whitespace-nowrap">{fmtDate(r.created_at)}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 text-xs font-medium capitalize ${
                          r.role === "professional" ? "text-amber-700" : "text-blue-700"
                        }`}>
                          {r.role === "professional" ? <Briefcase className="w-3.5 h-3.5" /> : <UserCheck className="w-3.5 h-3.5" />}
                          {r.role}
                        </span>
                      </td>
                      <td className="px-4 py-3 min-w-[180px]">
                        <p className="font-medium truncate max-w-[220px]">{r.name || "—"}</p>
                        <p className="text-xs text-muted-foreground truncate max-w-[220px]">
                          {r.email}
                          {r.user_display_id && <span className="ml-1">· {r.user_display_id}</span>}
                        </p>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap font-mono text-xs">{r.phone || "—"}</td>
                      <td className={`px-4 py-3 text-right font-semibold whitespace-nowrap ${
                        r.status === "completed" ? "text-green-700" : "text-muted-foreground"
                      }`}>
                        {fmtKsh(r.amount)}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs">{r.mpesa_receipt || "—"}</td>
                      <td className="px-4 py-3 font-mono text-xs">{r.reference || "—"}</td>
                      <td className="px-4 py-3"><StatusBadge status={r.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {totalPages > 1 && (
            <div className="flex items-center justify-between p-4 border-t border-border bg-muted/30">
              <span className="text-xs text-muted-foreground">
                Page {currentPage} of {totalPages}
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={filters.page === 0}
                  onClick={() => setFilters((p) => ({ ...p, page: p.page - 1 }))}
                  data-testid="page-prev"
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage >= totalPages}
                  onClick={() => setFilters((p) => ({ ...p, page: p.page + 1 }))}
                  data-testid="page-next"
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </Card>
      </main>
    </div>
  );
}

function SummaryCard({ label, value, sub, icon, tone, testId }) {
  const tones = {
    green: "bg-green-50 text-green-700 border-green-200",
    amber: "bg-amber-50 text-amber-800 border-amber-200",
    blue: "bg-blue-50 text-blue-700 border-blue-200",
    red: "bg-red-50 text-red-700 border-red-200",
    primary: "bg-primary/5 text-primary border-primary/20",
  };
  return (
    <Card className={`border ${tones[tone] || tones.primary}`} data-testid={testId}>
      <CardContent className="p-4 sm:p-5">
        <div className="flex items-center justify-between mb-1.5">
          <p className="text-xs uppercase tracking-wide font-medium opacity-80">{label}</p>
          <div className="opacity-70">{icon}</div>
        </div>
        <p className="font-heading font-bold text-xl sm:text-2xl truncate">{value}</p>
        <p className="text-[11px] mt-1 opacity-70 truncate">{sub}</p>
      </CardContent>
    </Card>
  );
}
