import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Badge } from "../components/ui/badge";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { 
  Users, DollarSign, Briefcase, TrendingUp, Calendar,
  LogOut, Home, ArrowUpRight, ArrowDownRight, ChevronRight
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, usersRes, transactionsRes] = await Promise.all([
          axios.get(`${API}/admin/stats`),
          axios.get(`${API}/admin/users`),
          axios.get(`${API}/admin/transactions`)
        ]);
        setStats(statsRes.data);
        setUsers(usersRes.data);
        setTransactions(transactionsRes.data);
      } catch (error) {
        console.error("Failed to fetch admin data:", error);
        toast.error("Failed to load admin data");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const statusColors = {
    pending: "bg-yellow-100 text-yellow-800",
    escrow: "bg-blue-100 text-blue-800",
    released: "bg-green-100 text-green-800",
    refunded: "bg-red-100 text-red-800"
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background" data-testid="admin-dashboard">
      <div className="flex">
        {/* Sidebar */}
        <aside className="hidden lg:flex flex-col w-64 min-h-screen bg-secondary text-secondary-foreground p-6">
          <div className="flex items-center gap-2 mb-8">
            <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
              <span className="text-primary-foreground font-heading font-bold text-xl">K</span>
            </div>
            <div>
              <span className="font-heading font-bold">Kazi Links</span>
              <p className="text-xs text-secondary-foreground/60">Admin Panel</p>
            </div>
          </div>

          <nav className="flex-1 space-y-2">
            <button 
              onClick={() => setActiveTab("overview")}
              className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors ${
                activeTab === "overview" ? "bg-primary/20 text-primary" : "hover:bg-white/10"
              }`}
            >
              <Home className="w-5 h-5" />
              <span>Overview</span>
            </button>
            <button 
              onClick={() => setActiveTab("users")}
              className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors ${
                activeTab === "users" ? "bg-primary/20 text-primary" : "hover:bg-white/10"
              }`}
            >
              <Users className="w-5 h-5" />
              <span>Users</span>
            </button>
            <button 
              onClick={() => setActiveTab("transactions")}
              className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors ${
                activeTab === "transactions" ? "bg-primary/20 text-primary" : "hover:bg-white/10"
              }`}
            >
              <DollarSign className="w-5 h-5" />
              <span>Transactions</span>
            </button>
          </nav>

          <div className="pt-6 border-t border-white/10">
            <button 
              onClick={handleLogout}
              className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-white/10 text-secondary-foreground/80 transition-colors"
              data-testid="logout-btn"
            >
              <LogOut className="w-5 h-5" />
              <span>Log out</span>
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-4 lg:p-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              <h1 className="font-heading text-2xl lg:text-3xl font-bold mb-2">Admin Dashboard</h1>
              <p className="text-muted-foreground">Monitor platform activity and manage users.</p>
            </div>

            {/* Mobile Tabs */}
            <div className="lg:hidden mb-6">
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="w-full">
                  <TabsTrigger value="overview" className="flex-1">Overview</TabsTrigger>
                  <TabsTrigger value="users" className="flex-1">Users</TabsTrigger>
                  <TabsTrigger value="transactions" className="flex-1">Transactions</TabsTrigger>
                </TabsList>
              </Tabs>
            </div>

            {/* Overview Tab */}
            {activeTab === "overview" && (
              <div className="space-y-6" data-testid="overview-section">
                {/* Stats Grid */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <Card className="border-border">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                          <Users className="w-5 h-5 text-blue-600" />
                        </div>
                        <ArrowUpRight className="w-4 h-4 text-green-500" />
                      </div>
                      <p className="text-2xl font-bold font-heading">{stats?.total_users || 0}</p>
                      <p className="text-sm text-muted-foreground">Total Users</p>
                    </CardContent>
                  </Card>

                  <Card className="border-border">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center">
                          <Briefcase className="w-5 h-5 text-primary" />
                        </div>
                        <ArrowUpRight className="w-4 h-4 text-green-500" />
                      </div>
                      <p className="text-2xl font-bold font-heading">{stats?.total_professionals || 0}</p>
                      <p className="text-sm text-muted-foreground">Professionals</p>
                    </CardContent>
                  </Card>

                  <Card className="border-border">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
                          <DollarSign className="w-5 h-5 text-emerald-600" />
                        </div>
                        <ArrowUpRight className="w-4 h-4 text-green-500" />
                      </div>
                      <p className="text-2xl font-bold font-heading">KSh {stats?.total_revenue?.toLocaleString() || 0}</p>
                      <p className="text-sm text-muted-foreground">Platform Revenue</p>
                    </CardContent>
                  </Card>

                  <Card className="border-border">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                          <TrendingUp className="w-5 h-5 text-purple-600" />
                        </div>
                        <ArrowUpRight className="w-4 h-4 text-green-500" />
                      </div>
                      <p className="text-2xl font-bold font-heading">{stats?.completed_bookings || 0}</p>
                      <p className="text-sm text-muted-foreground">Completed Jobs</p>
                    </CardContent>
                  </Card>
                </div>

                {/* Additional Stats */}
                <div className="grid lg:grid-cols-2 gap-6">
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle className="font-heading text-lg">Platform Statistics</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                        <span className="text-muted-foreground">Total Clients</span>
                        <span className="font-semibold">{stats?.total_clients || 0}</span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                        <span className="text-muted-foreground">Total Jobs Posted</span>
                        <span className="font-semibold">{stats?.total_jobs || 0}</span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                        <span className="text-muted-foreground">Total Bookings</span>
                        <span className="font-semibold">{stats?.total_bookings || 0}</span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                        <span className="text-muted-foreground">Total Transactions</span>
                        <span className="font-semibold">KSh {stats?.total_transactions?.toLocaleString() || 0}</span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-primary/10 rounded-lg">
                        <span className="text-muted-foreground">Platform Fee</span>
                        <span className="font-semibold text-primary">{stats?.platform_fee_percentage || 20}%</span>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-border">
                    <CardHeader className="flex flex-row items-center justify-between">
                      <CardTitle className="font-heading text-lg">Recent Transactions</CardTitle>
                      <button 
                        onClick={() => setActiveTab("transactions")}
                        className="text-primary text-sm hover:underline flex items-center gap-1"
                      >
                        View all <ChevronRight className="w-4 h-4" />
                      </button>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {transactions.slice(0, 5).map((tx) => (
                          <div key={tx.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                            <div>
                              <p className="font-medium text-sm">{tx.client_name} → {tx.professional_name}</p>
                              <p className="text-xs text-muted-foreground">
                                {new Date(tx.created_at).toLocaleDateString()}
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="font-semibold text-sm">KSh {tx.amount.toLocaleString()}</p>
                              <Badge className={`text-xs ${statusColors[tx.status]}`}>{tx.status}</Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            )}

            {/* Users Tab */}
            {activeTab === "users" && (
              <Card className="border-border" data-testid="users-section">
                <CardHeader>
                  <CardTitle className="font-heading text-lg">All Users ({users.length})</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-border">
                          <th className="text-left p-3 text-sm font-medium text-muted-foreground">Name</th>
                          <th className="text-left p-3 text-sm font-medium text-muted-foreground">Email</th>
                          <th className="text-left p-3 text-sm font-medium text-muted-foreground">Role</th>
                          <th className="text-left p-3 text-sm font-medium text-muted-foreground">Location</th>
                          <th className="text-left p-3 text-sm font-medium text-muted-foreground">Joined</th>
                        </tr>
                      </thead>
                      <tbody>
                        {users.map((u) => (
                          <tr key={u.id} className="border-b border-border/50 hover:bg-muted/50">
                            <td className="p-3 font-medium">{u.name}</td>
                            <td className="p-3 text-sm text-muted-foreground">{u.email}</td>
                            <td className="p-3">
                              <Badge className={
                                u.role === "admin" ? "bg-purple-100 text-purple-800" :
                                u.role === "professional" ? "bg-blue-100 text-blue-800" :
                                "bg-green-100 text-green-800"
                              }>
                                {u.role}
                              </Badge>
                            </td>
                            <td className="p-3 text-sm text-muted-foreground">{u.location || "N/A"}</td>
                            <td className="p-3 text-sm text-muted-foreground">
                              {new Date(u.created_at).toLocaleDateString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Transactions Tab */}
            {activeTab === "transactions" && (
              <Card className="border-border" data-testid="transactions-section">
                <CardHeader>
                  <CardTitle className="font-heading text-lg">All Transactions ({transactions.length})</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-border">
                          <th className="text-left p-3 text-sm font-medium text-muted-foreground">Date</th>
                          <th className="text-left p-3 text-sm font-medium text-muted-foreground">Client</th>
                          <th className="text-left p-3 text-sm font-medium text-muted-foreground">Professional</th>
                          <th className="text-left p-3 text-sm font-medium text-muted-foreground">Amount</th>
                          <th className="text-left p-3 text-sm font-medium text-muted-foreground">Platform Fee</th>
                          <th className="text-left p-3 text-sm font-medium text-muted-foreground">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {transactions.map((tx) => (
                          <tr key={tx.id} className="border-b border-border/50 hover:bg-muted/50">
                            <td className="p-3 text-sm">{new Date(tx.created_at).toLocaleDateString()}</td>
                            <td className="p-3 font-medium">{tx.client_name}</td>
                            <td className="p-3 font-medium">{tx.professional_name}</td>
                            <td className="p-3 text-sm">KSh {tx.amount.toLocaleString()}</td>
                            <td className="p-3 text-sm text-primary font-medium">
                              KSh {tx.platform_fee.toLocaleString()}
                            </td>
                            <td className="p-3">
                              <Badge className={statusColors[tx.status]}>{tx.status}</Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
