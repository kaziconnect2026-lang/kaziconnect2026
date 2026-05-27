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
  ArrowLeft, TrendingUp, TrendingDown, Wallet, Search, Filter,
  Loader2, Download, ArrowDownCircle, ArrowUpCircle, CheckCircle2,
  Clock, XCircle, RefreshCw,
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
      <CheckCircle2 className="w-3 h-3" />Completed
    </Badge>
  );
  if (status === "pending") return (
    <Badge className="bg-amber-100 text-amber-900 border-0 gap-1">
      <Clock className="w-3 h-3" />Pending
    </Badge>
  );
  if (status === "failed") return (
    <Badge className="bg-red-100 text-red-800 border-0 gap-1">
      <XCircle className="w-3 h-3" />Failed
    </Badge>
  );
  return <Badge variant="outline">{status}</Badge>;
}

export default function AdminTransactionsPage() {
  const navigate = useNavigate();
  const [data, setData] = useState({ transactions: [], summary: null, pagination: null });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    type: "all", status: "all", q: "", date_from: "", date_to: "", page: 0,
  });

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    if (filters.type !== "all") params.set("type", filters.type);
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
        const res = await axios.get(`${API}/admin/mpesa-transactions?${queryString}`);
        setData(res.data);
      } catch (err) {
        toast.error(err.response?.data?.detail || "Failed to load transactions");
      } finally {
        setLoading(false);
      }
    };
    const t = setTimeout(load, 250); // tiny debounce on text input
    return () => clearTimeout(t);
  }, [queryString]);

  const update = (patch) => setFilters((prev) => ({ ...prev, ...patch, page: 0 }));

  const exportCsv = () => {
    if (!data.transactions || data.transactions.length === 0) {
      toast.error("Nothing to export");
      return;
    }
    const headers = [
      "Date", "Type", "Status", "Amount (KSh)", "M-Pesa Receipt", "Reference",
      "Transaction ID", "Phone", "User Name", "User Email", "User Role", "Display ID",
    ];
    const rows = data.transactions.map((t) => [
      fmtDate(t.created_at),
      t.type,
      t.status,
      Number(t.amount || 0).toFixed(2),
      t.mpesa_receipt || "",
      t.reference || "",
      t.transaction_id || "",
      t.phone_number || t.user_phone || "",
      t.user_name || "",
      t.user_email || "",
      t.user_role || "",
      t.user_display_id || "",
    ]);
    const csv = [headers, ...rows]
      .map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(","))
      .join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    const stamp = new Date().toISOString().slice(0, 10);
    link.download = `kazi-links-mpesa-${stamp}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
    toast.success(`Exported ${rows.length} transactions`);
  };

  const s = data.summary || {};
  const totalPages = data.pagination ? Math.ceil(data.pagination.total / PAGE_SIZE) : 0;
  const currentPage = filters.page + 1;

  return (
    <div className="min-h-screen bg-background" data-testid="admin-transactions-page">
      <header className="sticky top-0 z-30 border-b border-border bg-background/95 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-3">
          <button onClick={() => navigate("/admin")} className="p-2 rounded-full hover:bg-muted" data-testid="back-btn">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <Wallet className="w-5 h-5 text-primary" />
          <h1 className="font-semibold text-lg">Platform Finances</h1>
          {data.pagination && (
            <Badge variant="outline" className="ml-2 text-xs">
              {data.pagination.total} transactions
            </Badge>
          )}
          <div className="ml-auto flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setFilters({ ...filters })}
              className="gap-2 rounded-lg"
              data-testid="refresh-btn"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button onClick={exportCsv} size="sm" className="gap-2 rounded-lg" data-testid="export-csv-btn">
              <Download className="w-4 h-4" />
              Export CSV
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Summary cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <SummaryCard
            label="Total Deposits"
            value={fmtKsh(s.deposits_completed?.total)}
            sub={`${s.deposits_completed?.count || 0} completed · ${(s.deposits_failed?.count || 0) + (s.deposits_pending?.count || 0)} pending/failed`}
            icon={<ArrowDownCircle className="w-5 h-5" />}
            tone="green"
            testId="summary-deposits"
          />
          <SummaryCard
            label="Total Withdrawals"
            value={fmtKsh(s.withdrawals_completed?.total)}
            sub={`${s.withdrawals_completed?.count || 0} completed · ${(s.withdrawals_failed?.count || 0) + (s.withdrawals_pending?.count || 0)} pending/failed`}
            icon={<ArrowUpCircle className="w-5 h-5" />}
            tone="amber"
            testId="summary-withdrawals"
          />
          <SummaryCard
            label="Net Platform Float"
            value={fmtKsh(s.net_flow)}
            sub="Deposits − Withdrawals"
            icon={s.net_flow >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
            tone={s.net_flow >= 0 ? "blue" : "red"}
            testId="summary-net-flow"
          />
          <SummaryCard
            label="Transactions"
            value={String(s.total_transactions || 0)}
            sub="Matching current filters"
            icon={<Wallet className="w-5 h-5" />}
            tone="primary"
            testId="summary-total-count"
          />
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="p-4 sm:p-5">
            <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3">
              <div className="relative lg:col-span-2">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search by name, email, M-Pesa ref, phone…"
                  value={filters.q}
                  onChange={(e) => update({ q: e.target.value })}
                  className="pl-9 h-10"
                  data-testid="txn-search"
                />
              </div>
              <Select value={filters.type} onValueChange={(v) => update({ type: v })}>
                <SelectTrigger className="h-10" data-testid="txn-type-filter"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All types</SelectItem>
                  <SelectItem value="deposit">Deposits</SelectItem>
                  <SelectItem value="withdrawal">Withdrawals</SelectItem>
                </SelectContent>
              </Select>
              <Select value={filters.status} onValueChange={(v) => update({ status: v })}>
                <SelectTrigger className="h-10" data-testid="txn-status-filter"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All statuses</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                </SelectContent>
              </Select>
              <div className="flex items-center gap-2">
                <Input
                  type="date"
                  value={filters.date_from}
                  onChange={(e) => update({ date_from: e.target.value })}
                  className="h-10"
                  data-testid="txn-date-from"
                  aria-label="From date"
                />
                <Input
                  type="date"
                  value={filters.date_to}
                  onChange={(e) => update({ date_to: e.target.value })}
                  className="h-10"
                  data-testid="txn-date-to"
                  aria-label="To date"
                />
              </div>
            </div>
            {(filters.type !== "all" || filters.status !== "all" || filters.q || filters.date_from || filters.date_to) && (
              <div className="flex items-center gap-2 mt-3">
                <Filter className="w-3 h-3 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">Filters active</span>
                <button
                  onClick={() => setFilters({ type: "all", status: "all", q: "", date_from: "", date_to: "", page: 0 })}
                  className="text-xs font-medium text-primary hover:underline"
                  data-testid="txn-clear-filters"
                >
                  Clear all
                </button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Transactions table */}
        <Card className="overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : data.transactions.length === 0 ? (
            <div className="text-center py-16 text-muted-foreground" data-testid="txn-empty">
              <Wallet className="w-12 h-12 mx-auto mb-3 opacity-40" />
              <p className="text-sm">No transactions match your filters.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="txn-table">
                <thead className="bg-muted/40 border-b border-border">
                  <tr className="text-left text-xs uppercase tracking-wide text-muted-foreground">
                    <th className="px-4 py-3 font-medium">Date</th>
                    <th className="px-4 py-3 font-medium">Type</th>
                    <th className="px-4 py-3 font-medium">User</th>
                    <th className="px-4 py-3 font-medium">Phone</th>
                    <th className="px-4 py-3 font-medium text-right">Amount</th>
                    <th className="px-4 py-3 font-medium">M-Pesa Receipt</th>
                    <th className="px-4 py-3 font-medium">Reference</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.transactions.map((t) => (
                    <tr
                      key={t.id || `${t.reference}-${t.created_at}`}
                      className="border-b border-border last:border-0 hover:bg-muted/20 transition-colors"
                      data-testid={`txn-row-${t.id || t.reference}`}
                    >
                      <td className="px-4 py-3 whitespace-nowrap">{fmtDate(t.created_at)}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 text-xs font-medium ${
                          t.type === "deposit" ? "text-green-700" : "text-amber-700"
                        }`}>
                          {t.type === "deposit"
                            ? <ArrowDownCircle className="w-3.5 h-3.5" />
                            : <ArrowUpCircle className="w-3.5 h-3.5" />}
                          {t.type === "deposit" ? "Deposit" : "Withdrawal"}
                        </span>
                      </td>
                      <td className="px-4 py-3 min-w-[160px]">
                        <p className="font-medium truncate max-w-[200px]">{t.user_name || "Unknown"}</p>
                        <p className="text-xs text-muted-foreground truncate max-w-[200px]">
                          {t.user_email || t.user_display_id || "—"}
                          {t.user_role && <span className="ml-1 capitalize">· {t.user_role}</span>}
                        </p>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap font-mono text-xs">{t.phone_number || "—"}</td>
                      <td className={`px-4 py-3 text-right font-semibold whitespace-nowrap ${
                        t.type === "deposit" ? "text-green-700" : "text-amber-700"
                      }`}>
                        {t.type === "deposit" ? "+" : "−"}{fmtKsh(t.amount)}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs">{t.mpesa_receipt || "—"}</td>
                      <td className="px-4 py-3 font-mono text-xs max-w-[180px] truncate" title={t.reference}>
                        {t.reference || "—"}
                      </td>
                      <td className="px-4 py-3"><StatusBadge status={t.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between p-4 border-t border-border bg-muted/30">
              <span className="text-xs text-muted-foreground">
                Page {currentPage} of {totalPages} · Showing {data.transactions.length} of {data.pagination.total}
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={filters.page === 0}
                  onClick={() => setFilters({ ...filters, page: filters.page - 1 })}
                  data-testid="page-prev"
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage >= totalPages}
                  onClick={() => setFilters({ ...filters, page: filters.page + 1 })}
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
