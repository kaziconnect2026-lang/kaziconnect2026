import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { 
  Search, Plus, Calendar, DollarSign, Clock, 
  MapPin, Star, ChevronRight, LogOut, Home,
  FileText, User, Bell, Menu, X
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ClientDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await axios.get(`${API}/dashboard/client`);
        setDashboardData(response.data);
      } catch (error) {
        console.error("Failed to fetch dashboard:", error);
        toast.error("Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const statusColors = {
    pending: "bg-yellow-100 text-yellow-800",
    confirmed: "bg-blue-100 text-blue-800",
    in_progress: "bg-purple-100 text-purple-800",
    completed: "bg-green-100 text-green-800",
    cancelled: "bg-red-100 text-red-800"
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background" data-testid="client-dashboard">
      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 glass border-b border-border/40">
        <div className="flex items-center justify-between px-4 h-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-primary-foreground font-heading font-bold">K</span>
            </div>
            <span className="font-heading font-bold">Kazi Links</span>
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
            <Link to="/client" className="flex items-center gap-3 p-3 rounded-xl bg-primary/10 text-primary">
              <Home className="w-5 h-5" />
              <span className="font-medium">Dashboard</span>
            </Link>
            <Link to="/search" className="flex items-center gap-3 p-3 rounded-xl hover:bg-muted">
              <Search className="w-5 h-5" />
              <span>Find Pros</span>
            </Link>
            <Link to="/post-job" className="flex items-center gap-3 p-3 rounded-xl hover:bg-muted">
              <Plus className="w-5 h-5" />
              <span>Post a Job</span>
            </Link>
            <Link to="/client/bookings" className="flex items-center gap-3 p-3 rounded-xl hover:bg-muted">
              <Calendar className="w-5 h-5" />
              <span>My Bookings</span>
            </Link>
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
            <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
              <span className="text-primary-foreground font-heading font-bold text-xl">K</span>
            </div>
            <span className="font-heading font-bold text-xl">Kazi Links</span>
          </div>

          <nav className="flex-1 space-y-2">
            <Link 
              to="/client" 
              className="flex items-center gap-3 p-3 rounded-xl bg-primary/10 text-primary font-medium"
              data-testid="nav-dashboard"
            >
              <Home className="w-5 h-5" />
              <span>Dashboard</span>
            </Link>
            <Link 
              to="/search" 
              className="flex items-center gap-3 p-3 rounded-xl hover:bg-muted transition-colors"
              data-testid="nav-search"
            >
              <Search className="w-5 h-5" />
              <span>Find Pros</span>
            </Link>
            <Link 
              to="/post-job" 
              className="flex items-center gap-3 p-3 rounded-xl hover:bg-muted transition-colors"
              data-testid="nav-post-job"
            >
              <Plus className="w-5 h-5" />
              <span>Post a Job</span>
            </Link>
            <Link 
              to="/client/bookings" 
              className="flex items-center gap-3 p-3 rounded-xl hover:bg-muted transition-colors"
              data-testid="nav-bookings"
            >
              <Calendar className="w-5 h-5" />
              <span>My Bookings</span>
            </Link>
          </nav>

          <div className="pt-6 border-t border-border">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-muted rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-muted-foreground" />
              </div>
              <div>
                <p className="font-medium text-sm">{user?.name}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
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
        <main className="flex-1 p-4 lg:p-8 pt-20 lg:pt-8">
          <div className="max-w-6xl mx-auto">
            {/* Welcome Header */}
            <div className="mb-8">
              <h1 className="font-heading text-2xl lg:text-3xl font-bold mb-2">
                Welcome back, {user?.name?.split(' ')[0]}!
              </h1>
              <p className="text-muted-foreground">Here's what's happening with your service requests.</p>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <Link to="/search">
                <Card className="h-full hover:shadow-card-hover transition-all cursor-pointer border-border">
                  <CardContent className="p-4 flex flex-col items-center text-center">
                    <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-3">
                      <Search className="w-6 h-6 text-primary" />
                    </div>
                    <span className="font-medium text-sm">Find a Pro</span>
                  </CardContent>
                </Card>
              </Link>
              <Link to="/post-job">
                <Card className="h-full hover:shadow-card-hover transition-all cursor-pointer border-border">
                  <CardContent className="p-4 flex flex-col items-center text-center">
                    <div className="w-12 h-12 bg-accent/10 rounded-xl flex items-center justify-center mb-3">
                      <Plus className="w-6 h-6 text-accent" />
                    </div>
                    <span className="font-medium text-sm">Post Job</span>
                  </CardContent>
                </Card>
              </Link>
              <Link to="/client/bookings">
                <Card className="h-full hover:shadow-card-hover transition-all cursor-pointer border-border">
                  <CardContent className="p-4 flex flex-col items-center text-center">
                    <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-3">
                      <Calendar className="w-6 h-6 text-blue-600" />
                    </div>
                    <span className="font-medium text-sm">Bookings</span>
                  </CardContent>
                </Card>
              </Link>
              <Card className="h-full border-border">
                <CardContent className="p-4 flex flex-col items-center text-center">
                  <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center mb-3">
                    <DollarSign className="w-6 h-6 text-emerald-600" />
                  </div>
                  <span className="font-medium text-sm">KSh {dashboardData?.total_spent?.toLocaleString() || 0}</span>
                  <span className="text-xs text-muted-foreground">Total Spent</span>
                </CardContent>
              </Card>
            </div>

            {/* Active Bookings */}
            <Card className="mb-8 border-border" data-testid="active-bookings-card">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="font-heading text-lg">Active Bookings</CardTitle>
                <Link to="/client/bookings" className="text-primary text-sm hover:underline flex items-center gap-1">
                  View all <ChevronRight className="w-4 h-4" />
                </Link>
              </CardHeader>
              <CardContent>
                {dashboardData?.active_bookings?.length > 0 ? (
                  <div className="space-y-4">
                    {dashboardData.active_bookings.map((booking) => (
                      <div 
                        key={booking.id} 
                        className="flex items-center justify-between p-4 bg-muted/50 rounded-xl"
                        data-testid={`booking-${booking.id}`}
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                            <User className="w-6 h-6 text-primary" />
                          </div>
                          <div>
                            <p className="font-medium">{booking.professional?.name || "Professional"}</p>
                            <p className="text-sm text-muted-foreground">{booking.service_description}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <Clock className="w-3 h-3 text-muted-foreground" />
                              <span className="text-xs text-muted-foreground">
                                {new Date(booking.scheduled_date).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge className={statusColors[booking.status]}>
                            {booking.status.replace('_', ' ')}
                          </Badge>
                          <p className="text-sm font-medium mt-2">KSh {booking.agreed_price.toLocaleString()}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Calendar className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground mb-4">No active bookings</p>
                    <Link to="/search">
                      <Button className="rounded-full" data-testid="find-pro-btn">Find a Professional</Button>
                    </Link>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Recent Jobs */}
            <Card className="border-border" data-testid="recent-jobs-card">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="font-heading text-lg">Recent Job Posts</CardTitle>
                <Link to="/post-job" className="text-primary text-sm hover:underline flex items-center gap-1">
                  Post new <Plus className="w-4 h-4" />
                </Link>
              </CardHeader>
              <CardContent>
                {dashboardData?.recent_jobs?.length > 0 ? (
                  <div className="space-y-4">
                    {dashboardData.recent_jobs.map((job) => (
                      <Link 
                        key={job.id} 
                        to={job.bid_count > 0 ? `/client/jobs/${job.id}/bids` : "#"}
                        className="block"
                      >
                        <div 
                          className={`flex items-center justify-between p-4 bg-muted/50 rounded-xl ${job.bid_count > 0 ? 'hover:bg-muted cursor-pointer' : ''}`}
                          data-testid={`job-${job.id}`}
                        >
                          <div>
                            <p className="font-medium">{job.title}</p>
                            <div className="flex items-center gap-3 mt-1">
                              <span className="text-sm text-muted-foreground">{job.category}</span>
                              <span className="text-sm text-muted-foreground flex items-center gap-1">
                                <MapPin className="w-3 h-3" /> {job.location}
                              </span>
                            </div>
                          </div>
                          <div className="text-right">
                            <Badge className={job.status === "open" ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}>
                              {job.status}
                            </Badge>
                            <p className="text-sm font-medium mt-2">KSh {job.budget.toLocaleString()}</p>
                            {job.bid_count > 0 && (
                              <p className="text-xs text-primary mt-1">
                                {job.bid_count} bid{job.bid_count !== 1 ? 's' : ''} received
                              </p>
                            )}
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground mb-4">No job posts yet</p>
                    <Link to="/post-job">
                      <Button className="rounded-full" data-testid="post-job-btn">Post Your First Job</Button>
                    </Link>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </main>
      </div>

      {/* Mobile Bottom Navigation */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 glass border-t border-border/40 px-6 py-3">
        <div className="flex items-center justify-around">
          <Link to="/client" className="flex flex-col items-center gap-1 text-primary">
            <Home className="w-5 h-5" />
            <span className="text-xs">Home</span>
          </Link>
          <Link to="/search" className="flex flex-col items-center gap-1 text-muted-foreground">
            <Search className="w-5 h-5" />
            <span className="text-xs">Search</span>
          </Link>
          <Link to="/post-job" className="flex flex-col items-center gap-1 text-muted-foreground">
            <Plus className="w-5 h-5" />
            <span className="text-xs">Post</span>
          </Link>
          <Link to="/client/bookings" className="flex flex-col items-center gap-1 text-muted-foreground">
            <Calendar className="w-5 h-5" />
            <span className="text-xs">Bookings</span>
          </Link>
        </div>
      </nav>
    </div>
  );
}
