import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { 
  ArrowLeft, ArrowDownCircle, ArrowUpCircle, Wallet, 
  FileText, Filter, Search, DollarSign, TrendingUp,
  Clock, CheckCircle2, Users, Briefcase
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function LedgerPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [ledger, setLedger] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    fetchLedger();
  }, [filterType]);

  const fetchLedger = async () => {
    try {
      const params = filterType !== "all" ? `?entry_type=${filterType}&limit=200` : "?limit=200";
      const response = await axios.get(`${API}/admin/ledger${params}`);
      setLedger(response.data);
    } catch (error) {
      console.error("Failed to fetch ledger:", error);
      toast.error("Failed to load ledger data");
    } finally {
      setLoading(false);
    }
  };

  const entryTypeConfig = {
    deposit: { icon: ArrowDownCircle, color: "text-green-600", bg: "bg-green-100", label: "Deposit" },
    withdrawal: { icon: ArrowUpCircle, color: "text-red-600", bg: "bg-red-100", label: "Withdrawal" },
    escrow_in: { icon: Wallet, color: "text-blue-600", bg: "bg-blue-100", label: "Escrow In" },
    escrow_out: { icon: Wallet, color: "text-purple-600", bg: "bg-purple-100", label: "Escrow Out" },
    platform_fee: { icon: DollarSign, color: "text-yellow-600", bg: "bg-yellow-100", label: "Platform Fee" },
    professional_payout: { icon: TrendingUp, color: "text-emerald-600", bg: "bg-emerald-100", label: "Pro Payout" },
    refund: { icon: ArrowDownCircle, color: "text-orange-600", bg: "bg-orange-100", label: "Refund" }
  };

  const filteredEntries = ledger?.entries?.filter(entry => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      entry.transaction_id?.toLowerCase().includes(q) ||
      entry.user_name?.toLowerCase().includes(q) ||
      entry.user_display_id?.toLowerCase().includes(q) ||
      entry.description?.toLowerCase().includes(q) ||
      entry.reference_id?.toLowerCase().includes(q)
    );
  }) || [];

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-20 lg:pb-0" data-testid="ledger-page">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-border/40">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-muted rounded-lg">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="font-heading font-semibold">Platform Ledger</h1>
          <Badge className="bg-primary/10 text-primary">
            {ledger?.total || 0} entries
          </Badge>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-6 gap-4 mb-6">
          <Card className="border-border">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <ArrowDownCircle className="w-4 h-4 text-green-600" />
                <span className="text-xs text-muted-foreground">Deposits</span>
              </div>
              <p className="text-lg font-bold">KSh {(ledger?.summary?.total_deposits || 0).toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">{ledger?.summary?.entry_counts?.deposit || 0} txns</p>
            </CardContent>
          </Card>
          
          <Card className="border-border">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <ArrowUpCircle className="w-4 h-4 text-red-600" />
                <span className="text-xs text-muted-foreground">Withdrawals</span>
              </div>
              <p className="text-lg font-bold">KSh {(ledger?.summary?.total_withdrawals || 0).toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">{ledger?.summary?.entry_counts?.withdrawal || 0} txns</p>
            </CardContent>
          </Card>
          
          <Card className="border-border">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Wallet className="w-4 h-4 text-blue-600" />
                <span className="text-xs text-muted-foreground">Escrow In</span>
              </div>
              <p className="text-lg font-bold">KSh {(ledger?.summary?.total_escrow_in || 0).toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">{ledger?.summary?.entry_counts?.escrow_in || 0} txns</p>
            </CardContent>
          </Card>
          
          <Card className="border-border">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Wallet className="w-4 h-4 text-purple-600" />
                <span className="text-xs text-muted-foreground">Escrow Out</span>
              </div>
              <p className="text-lg font-bold">KSh {(ledger?.summary?.total_escrow_out || 0).toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">{ledger?.summary?.entry_counts?.escrow_out || 0} txns</p>
            </CardContent>
          </Card>
          
          <Card className="border-border">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="w-4 h-4 text-yellow-600" />
                <span className="text-xs text-muted-foreground">Platform Fees</span>
              </div>
              <p className="text-lg font-bold text-yellow-600">KSh {(ledger?.summary?.total_platform_fees || 0).toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">{ledger?.summary?.entry_counts?.platform_fee || 0} txns</p>
            </CardContent>
          </Card>
          
          <Card className="border-border">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-emerald-600" />
                <span className="text-xs text-muted-foreground">Pro Payouts</span>
              </div>
              <p className="text-lg font-bold text-emerald-600">KSh {(ledger?.summary?.total_professional_payouts || 0).toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">{ledger?.summary?.entry_counts?.professional_payout || 0} txns</p>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4 mb-6">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search by ID, user, description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
              data-testid="ledger-search"
            />
          </div>
          <Select value={filterType} onValueChange={setFilterType}>
            <SelectTrigger className="w-48" data-testid="ledger-filter">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue placeholder="Filter by type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Transactions</SelectItem>
              <SelectItem value="deposit">Deposits</SelectItem>
              <SelectItem value="withdrawal">Withdrawals</SelectItem>
              <SelectItem value="escrow_in">Escrow In</SelectItem>
              <SelectItem value="escrow_out">Escrow Out</SelectItem>
              <SelectItem value="platform_fee">Platform Fees</SelectItem>
              <SelectItem value="professional_payout">Pro Payouts</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Ledger Table */}
        <Card className="border-border">
          <CardHeader>
            <CardTitle className="font-heading text-lg flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Transaction Ledger
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="text-left p-4 font-medium text-sm">Transaction ID</th>
                    <th className="text-left p-4 font-medium text-sm">Type</th>
                    <th className="text-left p-4 font-medium text-sm">User</th>
                    <th className="text-left p-4 font-medium text-sm">Related To</th>
                    <th className="text-right p-4 font-medium text-sm">Amount</th>
                    <th className="text-left p-4 font-medium text-sm">Description</th>
                    <th className="text-left p-4 font-medium text-sm">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEntries.map((entry) => {
                    const config = entryTypeConfig[entry.entry_type] || { icon: FileText, color: "text-gray-600", bg: "bg-gray-100", label: entry.entry_type };
                    const Icon = config.icon;
                    
                    return (
                      <tr key={entry.id} className="border-t border-border hover:bg-muted/30" data-testid={`ledger-${entry.id}`}>
                        <td className="p-4">
                          <code className="text-xs bg-muted px-2 py-1 rounded">{entry.transaction_id}</code>
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${config.bg}`}>
                              <Icon className={`w-4 h-4 ${config.color}`} />
                            </div>
                            <span className="text-sm font-medium">{config.label}</span>
                          </div>
                        </td>
                        <td className="p-4">
                          <div>
                            <p className="font-medium text-sm">{entry.user_name}</p>
                            <p className="text-xs text-muted-foreground">{entry.user_display_id}</p>
                          </div>
                        </td>
                        <td className="p-4">
                          {entry.related_user_name ? (
                            <div>
                              <p className="text-sm">{entry.related_user_name}</p>
                              <p className="text-xs text-muted-foreground">{entry.related_user_display_id}</p>
                            </div>
                          ) : (
                            <span className="text-muted-foreground text-sm">-</span>
                          )}
                        </td>
                        <td className="p-4 text-right">
                          <span className={`font-bold ${
                            ['deposit', 'professional_payout', 'refund'].includes(entry.entry_type) 
                              ? 'text-green-600' 
                              : ['withdrawal', 'escrow_in'].includes(entry.entry_type)
                              ? 'text-red-600'
                              : 'text-foreground'
                          }`}>
                            {['deposit', 'professional_payout', 'refund'].includes(entry.entry_type) ? '+' : 
                             ['withdrawal', 'escrow_in'].includes(entry.entry_type) ? '-' : ''}
                            KSh {entry.amount.toLocaleString()}
                          </span>
                        </td>
                        <td className="p-4">
                          <p className="text-sm text-muted-foreground max-w-xs truncate" title={entry.description}>
                            {entry.description}
                          </p>
                          {entry.reference_id && (
                            <p className="text-xs text-muted-foreground">Ref: {entry.reference_id}</p>
                          )}
                        </td>
                        <td className="p-4 text-sm text-muted-foreground">
                          {new Date(entry.created_at).toLocaleString()}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {filteredEntries.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No ledger entries found</p>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
