import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Switch } from "../components/ui/switch";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { 
  Home, Users, Briefcase, DollarSign, Star, TrendingUp, 
  Calendar, LogOut, Menu, X, BarChart3, PieChart, Activity,
  ArrowUpRight, ArrowDownRight, Search, Filter, CheckCircle2,
  Clock, XCircle, Wallet, Bell, Shield, ChevronRight, FileText, MessageCircle
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");
  const [userFilter, setUserFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [updatingUser, setUpdatingUser] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, dashboardRes, usersRes] = await Promise.all([
        axios.get(`${API}/admin/stats`),
        axios.get(`${API}/admin/dashboard`),
        axios.get(`${API}/admin/users?limit=100`)
      ]);
      setStats(statsRes.data);
      setDashboard(dashboardRes.data);
      setUsers(usersRes.data.users);
    } catch (error) {
      console.error("Failed to fetch admin data:", error);
      toast.error("Failed to load admin dashboard");
    } finally {
      setLoading(false);
    }
  };

  const handleUserStatusChange = async (userId, isActive) => {
    setUpdatingUser(userId);
    try {
      await axios.put(`${API}/admin/users/${userId}/status?is_active=${isActive}`);
      toast.success(`User ${isActive ? 'activated' : 'deactivated'} successfully`);
      setUsers(users.map(u => u.id === userId ? {...u, is_active: isActive} : u));
    } catch (error) {
      toast.error("Failed to update user status");
    } finally {
      setUpdatingUser(null);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const filteredUsers = users.filter(u => {
    const matchesRole = userFilter === "all" || u.role === userFilter;
    const matchesSearch = !searchQuery || 
      u.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.email.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesRole && matchesSearch;
  });

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  const StatCard = ({ title, value, icon: Icon, trend, color = "primary", subtitle }) => (
    <Card className="border-border hover:shadow-card-hover transition-all">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold font-heading mt-1">{value}</p>
            {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
          </div>
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center bg-${color}/10`}>
            <Icon className={`w-6 h-6 text-${color}`} />
          </div>
        </div>
        {trend !== undefined && (
          <div className={`flex items-center gap-1 mt-3 text-sm ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
            <span>{Math.abs(trend)}% from last week</span>
          </div>
        )}
      </CardContent>
    </Card>
  );

  const SimpleBarChart = ({ data, labels, title, color = "bg-primary" }) => {
    const maxValue = Math.max(...data, 1);
    return (
      <div>
        <p className="text-sm font-medium mb-4">{title}</p>
        <div className="flex items-end justify-between gap-2 h-32">
          {data.map((value, i) => {
            const height = (value / maxValue) * 100;
            return (
              <div key={i} className="flex-1 flex flex-col items-center gap-2">
                <span className="text-xs text-muted-foreground">{value}</span>
                <div className="w-full flex flex-col items-center justify-end h-24">
                  <div 
                    className={`w-full max-w-8 ${color} rounded-t-lg transition-all`}
                    style={{ height: `${Math.max(height, 4)}%` }}
                  />
                </div>
                <span className="text-xs text-muted-foreground">{labels[i]}</span>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-background" data-testid="admin-dashboard">
      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 glass border-b border-border/40">
        <div className="flex items-center justify-between px-4 h-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-red-600 rounded-lg flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="font-heading font-bold">Admin Panel</span>
          </div>
          <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="p-2">
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </header>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 z-40 bg-background pt-16">
          <nav className="p-4 space-y-2">
            <button onClick={() => { setActiveTab("overview"); setMobileMenuOpen(false); }} className={`w-full flex items-center gap-3 p-3 rounded-xl ${activeTab === "overview" ? "bg-primary/10 text-primary" : "hover:bg-muted"}`}>
              <Home className="w-5 h-5" />
              <span>Overview</span>
            </button>
            <button onClick={() => { setActiveTab("users"); setMobileMenuOpen(false); }} className={`w-full flex items-center gap-3 p-3 rounded-xl ${activeTab === "users" ? "bg-primary/10 text-primary" : "hover:bg-muted"}`}>
              <Users className="w-5 h-5" />
              <span>Users</span>
            </button>
            <button onClick={() => { setActiveTab("financials"); setMobileMenuOpen(false); }} className={`w-full flex items-center gap-3 p-3 rounded-xl ${activeTab === "financials" ? "bg-primary/10 text-primary" : "hover:bg-muted"}`}>
              <DollarSign className="w-5 h-5" />
              <span>Financials</span>
            </button>
            <button onClick={() => { setActiveTab("activity"); setMobileMenuOpen(false); }} className={`w-full flex items-center gap-3 p-3 rounded-xl ${activeTab === "activity" ? "bg-primary/10 text-primary" : "hover:bg-muted"}`}>
              <Activity className="w-5 h-5" />
              <span>Activity</span>
            </button>
            <button onClick={handleLogout} className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-destructive/10 text-destructive">
              <LogOut className="w-5 h-5" />
              <span>Log out</span>
            </button>
          </nav>
        </div>
      )}

      <div className="flex">
        {/* Desktop Sidebar */}
        <aside className="hidden lg:flex flex-col w-64 min-h-screen bg-card border-r border-border p-6">
          <div className="flex items-center gap-2 mb-8">
            <div className="w-10 h-10 bg-red-600 rounded-xl flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-heading font-bold">Kazi Links</span>
              <p className="text-xs text-muted-foreground">Admin Panel</p>
            </div>
          </div>

          <nav className="flex-1 space-y-2">
            <button 
              onClick={() => setActiveTab("overview")}
              className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors ${activeTab === "overview" ? "bg-primary/10 text-primary font-medium" : "hover:bg-muted"}`}
              data-testid="nav-overview"
            >
              <Home className="w-5 h-5" />
              <span>Overview</span>
            </button>
            <button 
              onClick={() => setActiveTab("users")}
              className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors ${activeTab === "users" ? "bg-primary/10 text-primary font-medium" : "hover:bg-muted"}`}
              data-testid="nav-users"
            >
              <Users className="w-5 h-5" />
              <span>Users</span>
              <Badge className="ml-auto bg-muted text-muted-foreground text-xs">
                {stats?.users?.total || 0}
              </Badge>
            </button>
            <button 
              onClick={() => setActiveTab("financials")}
              className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors ${activeTab === "financials" ? "bg-primary/10 text-primary font-medium" : "hover:bg-muted"}`}
              data-testid="nav-financials"
            >
              <DollarSign className="w-5 h-5" />
              <span>Financials</span>
            </button>
            <button 
              onClick={() => setActiveTab("activity")}
              className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors ${activeTab === "activity" ? "bg-primary/10 text-primary font-medium" : "hover:bg-muted"}`}
              data-testid="nav-activity"
            >
              <Activity className="w-5 h-5" />
              <span>Activity</span>
            </button>
            <Link 
              to="/admin/ledger"
              className="w-full flex items-center gap-3 p-3 rounded-xl transition-colors hover:bg-muted"
              data-testid="nav-ledger"
            >
              <FileText className="w-5 h-5" />
              <span>Ledger</span>
              <ChevronRight className="w-4 h-4 ml-auto" />
            </Link>
            <Link 
              to="/admin/conversations"
              className="w-full flex items-center gap-3 p-3 rounded-xl transition-colors hover:bg-muted"
              data-testid="nav-conversations"
            >
              <MessageCircle className="w-5 h-5" />
              <span>Chat Moderation</span>
              <ChevronRight className="w-4 h-4 ml-auto" />
            </Link>
            <Link 
              to="/admin/kyc"
              className="w-full flex items-center gap-3 p-3 rounded-xl transition-colors hover:bg-muted"
              data-testid="nav-kyc"
            >
              <Shield className="w-5 h-5" />
              <span>KYC Review</span>
              <ChevronRight className="w-4 h-4 ml-auto" />
            </Link>
          </nav>

          <div className="pt-6 border-t border-border">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                <Shield className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <p className="font-medium text-sm">{user?.name}</p>
                <p className="text-xs text-muted-foreground">Administrator</p>
              </div>
            </div>
            <button 
              onClick={handleLogout}
              className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-destructive/10 text-destructive transition-colors"
              data-testid="logout-btn"
            >
              <LogOut className="w-5 h-5" />
              <span>Log out</span>
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-4 lg:p-8 pt-20 lg:pt-8 pb-24 lg:pb-8">
          <div className="max-w-7xl mx-auto">
            
            {/* Overview Tab */}
            {activeTab === "overview" && (
              <>
                <div className="mb-8">
                  <h1 className="font-heading text-2xl lg:text-3xl font-bold mb-2">Dashboard Overview</h1>
                  <p className="text-muted-foreground">Monitor platform performance and key metrics</p>
                </div>

                {/* Key Metrics */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                  <StatCard 
                    title="Total Users" 
                    value={stats?.users?.total || 0}
                    icon={Users}
                    subtitle={`${stats?.users?.clients || 0} clients, ${stats?.users?.professionals || 0} pros`}
                  />
                  <StatCard 
                    title="Platform Revenue" 
                    value={`KSh ${(stats?.financials?.platform_revenue || 0).toLocaleString()}`}
                    icon={DollarSign}
                    color="emerald"
                    subtitle={`${stats?.financials?.platform_fee_percentage}% of transactions`}
                  />
                  <StatCard 
                    title="Total Jobs" 
                    value={stats?.jobs?.total || 0}
                    icon={Briefcase}
                    subtitle={`${stats?.jobs?.open || 0} open, ${stats?.jobs?.completed || 0} completed`}
                  />
                  <StatCard 
                    title="Avg. Rating" 
                    value={`${stats?.reviews?.average_rating || 0}/5`}
                    icon={Star}
                    color="yellow"
                    subtitle={`${stats?.reviews?.total || 0} total reviews`}
                  />
                </div>

                {/* Charts Row */}
                <div className="grid lg:grid-cols-2 gap-6 mb-8">
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle className="font-heading text-lg flex items-center gap-2">
                        <BarChart3 className="w-5 h-5" />
                        Daily Revenue (Last 7 Days)
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <SimpleBarChart 
                        data={dashboard?.charts?.revenue || [0,0,0,0,0,0,0]}
                        labels={dashboard?.charts?.labels || ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']}
                        title=""
                        color="bg-emerald-500"
                      />
                      <div className="mt-4 pt-4 border-t border-border">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Total (7 days)</span>
                          <span className="font-bold">
                            KSh {(dashboard?.charts?.revenue?.reduce((a,b) => a+b, 0) || 0).toLocaleString()}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle className="font-heading text-lg flex items-center gap-2">
                        <TrendingUp className="w-5 h-5" />
                        Daily Bookings (Last 7 Days)
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <SimpleBarChart 
                        data={dashboard?.charts?.bookings || [0,0,0,0,0,0,0]}
                        labels={dashboard?.charts?.labels || ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']}
                        title=""
                        color="bg-blue-500"
                      />
                      <div className="mt-4 pt-4 border-t border-border">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Total (7 days)</span>
                          <span className="font-bold">
                            {(dashboard?.charts?.bookings?.reduce((a,b) => a+b, 0) || 0)} bookings
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Secondary Stats */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                  <Card className="border-border">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-yellow-100 rounded-xl flex items-center justify-center">
                          <Clock className="w-5 h-5 text-yellow-600" />
                        </div>
                        <div>
                          <p className="text-2xl font-bold">{stats?.bookings?.pending || 0}</p>
                          <p className="text-xs text-muted-foreground">Pending Bookings</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="border-border">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                          <Activity className="w-5 h-5 text-purple-600" />
                        </div>
                        <div>
                          <p className="text-2xl font-bold">{stats?.bookings?.in_progress || 0}</p>
                          <p className="text-xs text-muted-foreground">In Progress</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="border-border">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
                          <CheckCircle2 className="w-5 h-5 text-green-600" />
                        </div>
                        <div>
                          <p className="text-2xl font-bold">{stats?.bids?.acceptance_rate || 0}%</p>
                          <p className="text-xs text-muted-foreground">Bid Acceptance</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="border-border">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                          <Users className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                          <p className="text-2xl font-bold">{stats?.users?.active_professionals || 0}</p>
                          <p className="text-xs text-muted-foreground">Active Pros</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Top Performers */}
                <div className="grid lg:grid-cols-2 gap-6">
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle className="font-heading text-lg flex items-center gap-2">
                        <Star className="w-5 h-5 text-yellow-500" />
                        Top Rated Professionals
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {dashboard?.top_professionals?.length > 0 ? (
                        <div className="space-y-3">
                          {dashboard.top_professionals.map((prof, i) => (
                            <div key={i} className="flex items-center justify-between p-3 bg-muted/50 rounded-xl">
                              <div className="flex items-center gap-3">
                                <span className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-xs font-bold">
                                  {i + 1}
                                </span>
                                <div>
                                  <p className="font-medium text-sm">{prof.name}</p>
                                  <p className="text-xs text-muted-foreground">{prof.profession}</p>
                                </div>
                              </div>
                              <div className="flex items-center gap-1">
                                <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                                <span className="font-bold">{prof.rating?.toFixed(1)}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-center py-8 text-muted-foreground">No rated professionals yet</p>
                      )}
                    </CardContent>
                  </Card>

                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle className="font-heading text-lg flex items-center gap-2">
                        <DollarSign className="w-5 h-5 text-emerald-500" />
                        Top Earners
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {dashboard?.top_earners?.length > 0 ? (
                        <div className="space-y-3">
                          {dashboard.top_earners.map((prof, i) => (
                            <div key={i} className="flex items-center justify-between p-3 bg-muted/50 rounded-xl">
                              <div className="flex items-center gap-3">
                                <span className="w-6 h-6 bg-emerald-100 rounded-full flex items-center justify-center text-xs font-bold text-emerald-600">
                                  {i + 1}
                                </span>
                                <div>
                                  <p className="font-medium text-sm">{prof.name}</p>
                                  <p className="text-xs text-muted-foreground">{prof.profession}</p>
                                </div>
                              </div>
                              <span className="font-bold text-emerald-600">
                                KSh {prof.total_earnings?.toLocaleString()}
                              </span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-center py-8 text-muted-foreground">No earnings recorded yet</p>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </>
            )}

            {/* Users Tab */}
            {activeTab === "users" && (
              <>
                <div className="mb-8">
                  <h1 className="font-heading text-2xl lg:text-3xl font-bold mb-2">User Management</h1>
                  <p className="text-muted-foreground">View and manage all platform users</p>
                </div>

                {/* Filters */}
                <div className="flex flex-wrap items-center gap-4 mb-6">
                  <div className="relative flex-1 min-w-[200px]">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      placeholder="Search users..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10"
                      data-testid="user-search"
                    />
                  </div>
                  <Select value={userFilter} onValueChange={setUserFilter}>
                    <SelectTrigger className="w-40" data-testid="user-filter">
                      <SelectValue placeholder="Filter by role" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Users</SelectItem>
                      <SelectItem value="client">Clients</SelectItem>
                      <SelectItem value="professional">Professionals</SelectItem>
                      <SelectItem value="admin">Admins</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* User Stats */}
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <Card className="border-border">
                    <CardContent className="p-4 text-center">
                      <p className="text-2xl font-bold">{stats?.users?.clients || 0}</p>
                      <p className="text-xs text-muted-foreground">Clients</p>
                    </CardContent>
                  </Card>
                  <Card className="border-border">
                    <CardContent className="p-4 text-center">
                      <p className="text-2xl font-bold">{stats?.users?.professionals || 0}</p>
                      <p className="text-xs text-muted-foreground">Professionals</p>
                    </CardContent>
                  </Card>
                  <Card className="border-border">
                    <CardContent className="p-4 text-center">
                      <p className="text-2xl font-bold">{stats?.users?.active_professionals || 0}</p>
                      <p className="text-xs text-muted-foreground">Active Pros</p>
                    </CardContent>
                  </Card>
                </div>

                {/* Users Table */}
                <Card className="border-border">
                  <CardContent className="p-0">
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-muted/50">
                          <tr>
                            <th className="text-left p-4 font-medium text-sm">User</th>
                            <th className="text-left p-4 font-medium text-sm">Role</th>
                            <th className="text-left p-4 font-medium text-sm">Location</th>
                            <th className="text-left p-4 font-medium text-sm">Wallet</th>
                            <th className="text-left p-4 font-medium text-sm">Status</th>
                            <th className="text-left p-4 font-medium text-sm">Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredUsers.map((u) => (
                            <tr key={u.id} className="border-t border-border" data-testid={`user-row-${u.id}`}>
                              <td className="p-4">
                                <div>
                                  <p className="font-medium">{u.name}</p>
                                  <p className="text-sm text-muted-foreground">{u.email}</p>
                                </div>
                              </td>
                              <td className="p-4">
                                <Badge className={
                                  u.role === "admin" ? "bg-red-100 text-red-800" :
                                  u.role === "professional" ? "bg-blue-100 text-blue-800" :
                                  "bg-green-100 text-green-800"
                                }>
                                  {u.role}
                                </Badge>
                              </td>
                              <td className="p-4 text-sm text-muted-foreground">
                                {u.location || "N/A"}
                              </td>
                              <td className="p-4 text-sm">
                                KSh {(u.wallet_balance || 0).toLocaleString()}
                              </td>
                              <td className="p-4">
                                <Badge className={u.is_active !== false ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
                                  {u.is_active !== false ? "Active" : "Inactive"}
                                </Badge>
                              </td>
                              <td className="p-4">
                                <Switch
                                  checked={u.is_active !== false}
                                  onCheckedChange={(checked) => handleUserStatusChange(u.id, checked)}
                                  disabled={updatingUser === u.id || u.role === "admin"}
                                  data-testid={`toggle-${u.id}`}
                                />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {filteredUsers.length === 0 && (
                      <div className="text-center py-12 text-muted-foreground">
                        No users found
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            )}

            {/* Financials Tab */}
            {activeTab === "financials" && (
              <>
                <div className="mb-8">
                  <h1 className="font-heading text-2xl lg:text-3xl font-bold mb-2">Financial Overview</h1>
                  <p className="text-muted-foreground">Track platform revenue and transactions</p>
                </div>

                {/* Financial Stats */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                  <StatCard 
                    title="Total Transactions" 
                    value={`KSh ${(stats?.financials?.total_transactions || 0).toLocaleString()}`}
                    icon={DollarSign}
                    color="blue"
                  />
                  <StatCard 
                    title="Platform Revenue" 
                    value={`KSh ${(stats?.financials?.platform_revenue || 0).toLocaleString()}`}
                    icon={TrendingUp}
                    color="emerald"
                    subtitle={`${stats?.financials?.platform_fee_percentage}% commission`}
                  />
                  <StatCard 
                    title="Escrow Balance" 
                    value={`KSh ${(stats?.financials?.escrow_balance || 0).toLocaleString()}`}
                    icon={Wallet}
                    color="yellow"
                    subtitle="Awaiting release"
                  />
                  <StatCard 
                    title="Wallet Deposits" 
                    value={`KSh ${(stats?.financials?.total_wallet_deposits || 0).toLocaleString()}`}
                    icon={Wallet}
                    color="purple"
                  />
                </div>

                {/* Booking Status Breakdown */}
                <Card className="border-border mb-8">
                  <CardHeader>
                    <CardTitle className="font-heading text-lg">Booking Status Breakdown</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
                      <div className="p-4 bg-yellow-50 rounded-xl text-center">
                        <p className="text-2xl font-bold text-yellow-600">{stats?.bookings?.pending || 0}</p>
                        <p className="text-sm text-yellow-800">Pending</p>
                      </div>
                      <div className="p-4 bg-blue-50 rounded-xl text-center">
                        <p className="text-2xl font-bold text-blue-600">{stats?.bookings?.confirmed || 0}</p>
                        <p className="text-sm text-blue-800">Confirmed</p>
                      </div>
                      <div className="p-4 bg-purple-50 rounded-xl text-center">
                        <p className="text-2xl font-bold text-purple-600">{stats?.bookings?.in_progress || 0}</p>
                        <p className="text-sm text-purple-800">In Progress</p>
                      </div>
                      <div className="p-4 bg-green-50 rounded-xl text-center">
                        <p className="text-2xl font-bold text-green-600">{stats?.bookings?.completed || 0}</p>
                        <p className="text-sm text-green-800">Completed</p>
                      </div>
                      <div className="p-4 bg-red-50 rounded-xl text-center">
                        <p className="text-2xl font-bold text-red-600">{stats?.bookings?.cancelled || 0}</p>
                        <p className="text-sm text-red-800">Cancelled</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Bid Stats */}
                <Card className="border-border">
                  <CardHeader>
                    <CardTitle className="font-heading text-lg">Bid Statistics</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                      <div className="p-4 bg-muted/50 rounded-xl">
                        <p className="text-2xl font-bold">{stats?.bids?.total || 0}</p>
                        <p className="text-sm text-muted-foreground">Total Bids</p>
                      </div>
                      <div className="p-4 bg-yellow-50 rounded-xl">
                        <p className="text-2xl font-bold text-yellow-600">{stats?.bids?.pending || 0}</p>
                        <p className="text-sm text-yellow-800">Pending</p>
                      </div>
                      <div className="p-4 bg-green-50 rounded-xl">
                        <p className="text-2xl font-bold text-green-600">{stats?.bids?.accepted || 0}</p>
                        <p className="text-sm text-green-800">Accepted</p>
                      </div>
                      <div className="p-4 bg-primary/10 rounded-xl">
                        <p className="text-2xl font-bold text-primary">{stats?.bids?.acceptance_rate || 0}%</p>
                        <p className="text-sm text-muted-foreground">Acceptance Rate</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}

            {/* Activity Tab */}
            {activeTab === "activity" && (
              <>
                <div className="mb-8">
                  <h1 className="font-heading text-2xl lg:text-3xl font-bold mb-2">Recent Activity</h1>
                  <p className="text-muted-foreground">Monitor platform activity in real-time</p>
                </div>

                <div className="grid lg:grid-cols-2 gap-6">
                  {/* Recent Bookings */}
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle className="font-heading text-lg flex items-center gap-2">
                        <Calendar className="w-5 h-5" />
                        Recent Bookings
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {dashboard?.recent_activity?.bookings?.length > 0 ? (
                        <div className="space-y-3">
                          {dashboard.recent_activity.bookings.map((booking) => (
                            <div key={booking.id} className="p-3 bg-muted/50 rounded-xl">
                              <div className="flex items-center justify-between mb-2">
                                <p className="font-medium text-sm">{booking.service_description}</p>
                                <Badge className={
                                  booking.status === "completed" ? "bg-green-100 text-green-800" :
                                  booking.status === "pending" ? "bg-yellow-100 text-yellow-800" :
                                  "bg-blue-100 text-blue-800"
                                }>
                                  {booking.status}
                                </Badge>
                              </div>
                              <div className="flex items-center justify-between text-xs text-muted-foreground">
                                <span>{booking.client_name} → {booking.professional_name}</span>
                                <span>KSh {booking.agreed_price?.toLocaleString()}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-center py-8 text-muted-foreground">No recent bookings</p>
                      )}
                    </CardContent>
                  </Card>

                  {/* Recent Jobs */}
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle className="font-heading text-lg flex items-center gap-2">
                        <Briefcase className="w-5 h-5" />
                        Recent Jobs Posted
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {dashboard?.recent_activity?.jobs?.length > 0 ? (
                        <div className="space-y-3">
                          {dashboard.recent_activity.jobs.map((job) => (
                            <div key={job.id} className="p-3 bg-muted/50 rounded-xl">
                              <div className="flex items-center justify-between mb-2">
                                <p className="font-medium text-sm">{job.title}</p>
                                <Badge variant="outline">{job.category}</Badge>
                              </div>
                              <div className="flex items-center justify-between text-xs text-muted-foreground">
                                <span>{job.location}</span>
                                <span>Budget: KSh {job.budget?.toLocaleString()}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-center py-8 text-muted-foreground">No recent jobs</p>
                      )}
                    </CardContent>
                  </Card>

                  {/* Jobs by Category */}
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle className="font-heading text-lg flex items-center gap-2">
                        <PieChart className="w-5 h-5" />
                        Jobs by Category
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {dashboard?.jobs_by_category?.length > 0 ? (
                        <div className="space-y-3">
                          {dashboard.jobs_by_category.map((cat, i) => (
                            <div key={i} className="flex items-center justify-between p-3 bg-muted/50 rounded-xl">
                              <span className="font-medium text-sm capitalize">{cat.category}</span>
                              <Badge variant="outline">{cat.count} jobs</Badge>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-center py-8 text-muted-foreground">No jobs yet</p>
                      )}
                    </CardContent>
                  </Card>

                  {/* New Users */}
                  <Card className="border-border">
                    <CardHeader>
                      <CardTitle className="font-heading text-lg flex items-center gap-2">
                        <Users className="w-5 h-5" />
                        New Users (Last 30 Days)
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <SimpleBarChart 
                        data={dashboard?.charts?.new_users || [0,0,0,0,0,0,0]}
                        labels={dashboard?.charts?.labels || ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']}
                        title=""
                        color="bg-primary"
                      />
                    </CardContent>
                  </Card>
                </div>
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
