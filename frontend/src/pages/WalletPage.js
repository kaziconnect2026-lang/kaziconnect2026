import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { Label } from "../components/ui/label";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { 
  ArrowLeft, Wallet, ArrowDownCircle, ArrowUpCircle, 
  Clock, CheckCircle2, AlertCircle, Phone
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function WalletPage() {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [depositOpen, setDepositOpen] = useState(false);
  const [withdrawOpen, setWithdrawOpen] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [depositData, setDepositData] = useState({ amount: "", phone_number: "" });
  const [withdrawData, setWithdrawData] = useState({ amount: "", phone_number: "" });

  useEffect(() => {
    fetchWalletData();
  }, []);

  const fetchWalletData = async () => {
    try {
      const [balanceRes, transactionsRes] = await Promise.all([
        axios.get(`${API}/wallet/balance`),
        axios.get(`${API}/wallet/transactions`)
      ]);
      setBalance(balanceRes.data.balance);
      setTransactions(transactionsRes.data);
    } catch (error) {
      console.error("Failed to fetch wallet data:", error);
      toast.error("Failed to load wallet data");
    } finally {
      setLoading(false);
    }
  };

  const handleDeposit = async (e) => {
    e.preventDefault();
    if (!depositData.amount || parseFloat(depositData.amount) <= 0) {
      toast.error("Please enter a valid amount");
      return;
    }
    
    setProcessing(true);
    try {
      const response = await axios.post(`${API}/wallet/deposit`, {
        amount: parseFloat(depositData.amount),
        phone_number: depositData.phone_number || user?.phone || "254712345678"
      });
      
      toast.success(`Deposited KSh ${parseFloat(depositData.amount).toLocaleString()}`);
      setBalance(response.data.new_balance);
      setDepositOpen(false);
      setDepositData({ amount: "", phone_number: "" });
      fetchWalletData();
      if (refreshUser) refreshUser();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Deposit failed");
    } finally {
      setProcessing(false);
    }
  };

  const handleWithdraw = async (e) => {
    e.preventDefault();
    if (!withdrawData.amount || parseFloat(withdrawData.amount) <= 0) {
      toast.error("Please enter a valid amount");
      return;
    }
    if (parseFloat(withdrawData.amount) > balance) {
      toast.error("Insufficient balance");
      return;
    }
    
    setProcessing(true);
    try {
      const response = await axios.post(`${API}/wallet/withdraw`, {
        amount: parseFloat(withdrawData.amount),
        phone_number: withdrawData.phone_number || user?.phone || "254712345678"
      });
      
      toast.success(`Withdrawn KSh ${parseFloat(withdrawData.amount).toLocaleString()} to M-Pesa`);
      setBalance(response.data.new_balance);
      setWithdrawOpen(false);
      setWithdrawData({ amount: "", phone_number: "" });
      fetchWalletData();
      if (refreshUser) refreshUser();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Withdrawal failed");
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-20 lg:pb-0" data-testid="wallet-page">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-border/40">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-muted rounded-lg">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="font-heading font-semibold">My Wallet</h1>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6">
        {/* Balance Card */}
        <Card className="border-border mb-6 bg-gradient-to-br from-primary/10 to-primary/5" data-testid="balance-card">
          <CardContent className="p-8 text-center">
            <div className="w-16 h-16 bg-primary/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Wallet className="w-8 h-8 text-primary" />
            </div>
            <p className="text-sm text-muted-foreground mb-2">Available Balance</p>
            <p className="text-4xl font-bold font-heading text-primary" data-testid="balance-amount">
              KSh {balance.toLocaleString()}
            </p>
            
            <div className="flex justify-center gap-4 mt-6">
              <Dialog open={depositOpen} onOpenChange={setDepositOpen}>
                <DialogTrigger asChild>
                  <Button className="rounded-xl gap-2" data-testid="deposit-btn">
                    <ArrowDownCircle className="w-4 h-4" />
                    Deposit
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle className="font-heading">Deposit to Wallet</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleDeposit} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>Amount (KSh)</Label>
                      <Input
                        type="number"
                        placeholder="Enter amount"
                        value={depositData.amount}
                        onChange={(e) => setDepositData({...depositData, amount: e.target.value})}
                        required
                        min="1"
                        max="100000"
                        className="h-12 text-lg"
                        data-testid="deposit-amount-input"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label>M-Pesa Phone Number</Label>
                      <div className="relative">
                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <Input
                          type="tel"
                          placeholder="254712345678"
                          value={depositData.phone_number}
                          onChange={(e) => setDepositData({...depositData, phone_number: e.target.value})}
                          className="h-12 pl-10"
                          data-testid="deposit-phone-input"
                        />
                      </div>
                    </div>
                    
                    <div className="p-3 bg-yellow-50 rounded-xl text-sm">
                      <p className="flex items-center gap-2 text-yellow-800">
                        <AlertCircle className="w-4 h-4" />
                        M-Pesa deposit is MOCKED for demo
                      </p>
                    </div>
                    
                    <Button 
                      type="submit" 
                      className="w-full h-12 rounded-xl"
                      disabled={processing}
                      data-testid="confirm-deposit-btn"
                    >
                      {processing ? "Processing..." : "Confirm Deposit"}
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
              
              <Dialog open={withdrawOpen} onOpenChange={setWithdrawOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="rounded-xl gap-2" data-testid="withdraw-btn">
                    <ArrowUpCircle className="w-4 h-4" />
                    Withdraw
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle className="font-heading">Withdraw to M-Pesa</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleWithdraw} className="space-y-4 mt-4">
                    <div className="p-3 bg-muted/50 rounded-xl">
                      <p className="text-sm text-muted-foreground">Available Balance</p>
                      <p className="text-xl font-bold">KSh {balance.toLocaleString()}</p>
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Amount (KSh)</Label>
                      <Input
                        type="number"
                        placeholder="Enter amount"
                        value={withdrawData.amount}
                        onChange={(e) => setWithdrawData({...withdrawData, amount: e.target.value})}
                        required
                        min="1"
                        max={balance}
                        className="h-12 text-lg"
                        data-testid="withdraw-amount-input"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label>M-Pesa Phone Number</Label>
                      <div className="relative">
                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <Input
                          type="tel"
                          placeholder="254712345678"
                          value={withdrawData.phone_number}
                          onChange={(e) => setWithdrawData({...withdrawData, phone_number: e.target.value})}
                          className="h-12 pl-10"
                          data-testid="withdraw-phone-input"
                        />
                      </div>
                    </div>
                    
                    <div className="p-3 bg-yellow-50 rounded-xl text-sm">
                      <p className="flex items-center gap-2 text-yellow-800">
                        <AlertCircle className="w-4 h-4" />
                        M-Pesa withdrawal is MOCKED for demo
                      </p>
                    </div>
                    
                    <Button 
                      type="submit" 
                      className="w-full h-12 rounded-xl"
                      disabled={processing}
                      data-testid="confirm-withdraw-btn"
                    >
                      {processing ? "Processing..." : "Confirm Withdrawal"}
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
            </div>
          </CardContent>
        </Card>

        {/* Transaction History */}
        <Card className="border-border" data-testid="transactions-card">
          <CardHeader>
            <CardTitle className="font-heading text-lg">Transaction History</CardTitle>
          </CardHeader>
          <CardContent>
            {transactions.length > 0 ? (
              <div className="space-y-3">
                {transactions.map((tx) => (
                  <div 
                    key={tx.id}
                    className="flex items-center justify-between p-4 bg-muted/50 rounded-xl"
                    data-testid={`transaction-${tx.id}`}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                        tx.type === "deposit" ? "bg-green-100" : "bg-red-100"
                      }`}>
                        {tx.type === "deposit" ? (
                          <ArrowDownCircle className="w-5 h-5 text-green-600" />
                        ) : (
                          <ArrowUpCircle className="w-5 h-5 text-red-600" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium capitalize">{tx.type}</p>
                        <p className="text-xs text-muted-foreground">{tx.reference}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(tx.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`font-bold ${tx.type === "deposit" ? "text-green-600" : "text-red-600"}`}>
                        {tx.type === "deposit" ? "+" : "-"}KSh {tx.amount.toLocaleString()}
                      </p>
                      <Badge className={tx.status === "completed" ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"}>
                        {tx.status === "completed" ? <CheckCircle2 className="w-3 h-3 mr-1" /> : <Clock className="w-3 h-3 mr-1" />}
                        {tx.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Clock className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">No transactions yet</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Deposit funds to your wallet to get started
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
