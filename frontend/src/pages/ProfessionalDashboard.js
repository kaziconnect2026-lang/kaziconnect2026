import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Switch } from "../components/ui/switch";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { 
  Home, Calendar, DollarSign, Star, TrendingUp, Clock,
  User, LogOut, Menu, X, Settings, Briefcase, ChevronRight,
  AlertCircle, CheckCircle2
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ProfessionalDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [availability, setAvailability] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [hasProfile, setHasProfile] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await axios.get(`${API}/dashboard/professional`);
        setDashboardData(response.data);
        if (response.data.profile) {
          setAvailability(response.data.profile.availability);
        } else {
          setHasProfile(false);
        }
      } catch (error) {
        console.error("Failed to fetch dashboard:", error);
        if (error.response?.status === 404) {
          setHasProfile(false);
        }
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

  const handleAvailabilityToggle = async (checked) => {
    try {
      await axios.put(`${API}/professionals/availability?available=${checked}`);
      setAvailability(checked);
      toast.success(checked ? "You're now available for bookings" : "You're now offline");
    } catch (error) {
      toast.error("Failed to update availability");
    }
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

  // Show profile creation prompt if no profile
  if (!hasProfile) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4" data-testid="no-profile-prompt">
        <Card className="max-w-md w-full border-border">
          <CardContent className="p-8 text-center">
            <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <Briefcase className="w-8 h-8 text-primary" />
            </div>
            <h2 className="font-heading text-2xl font-bold mb-2">Complete Your Profile</h2>
            <p className="text-muted-foreground mb-6">
              Set up your professional profile to start receiving bookings from clients.
            </p>
            <Link to="/create-profile">
              <Button className="w-full rounded-xl h-12" data-testid="create-profile-btn">
                Create Profile
              </Button>
            </Link>
            <button 
              onClick={handleLogout}
              className="w-full mt-4 text-sm text-muted-foreground hover:text-foreground"
            >
              Log out
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background" data-testid="professional-dashboard">
      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 glass border-b border-border/40">
        <div className="flex items-center justify-between px-4 h-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-primary-foreground font-heading font-bold">K</span>
            </div>
            <span className="font-heading font-bold">Pro Dashboard</span>
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
            <Link to="/professional" className="flex items-center gap-3 p-3 rounded-xl bg-primary/10 text-primary">
              <Home className="w-5 h-5" />
              <span className="font-medium">Dashboard</span>
            </Link>
            <Link to="/professional/bookings" className="flex items-center gap-3 p-3 rounded-xl hover:bg-muted">
              <Calendar className="w-5 h-5" />
              <span>My Bookings</span>
            </Link>
            <Link to="/create-profile" className="flex items-center gap-3 p-3 rounded-xl hover:bg-muted">
              <Settings className="w-5 h-5" />
              <span>Edit Profile</span>
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
            <div>
              <span className="font-heading font-bold">Kazi Links</span>
              <p className="text-xs text-muted-foreground">Pro Dashboard</p>
            </div>
          </div>

          <nav className="flex-1 space-y-2">
            <Link 
              to="/professional" 
              className="flex items-center gap-3 p-3 rounded-xl bg-primary/10 text-primary font-medium"
              data-testid="nav-dashboard"
            >
              <Home className="w-5 h-5" />
              <span>Dashboard</span>
            </Link>
            <Link 
              to="/professional/bookings" 
              className="flex items-center gap-3 p-3 rounded-xl hover:bg-muted transition-colors"
              data-testid="nav-bookings"
            >
              <Calendar className="w-5 h-5" />
              <span>My Bookings</span>
            </Link>
            <Link 
              to="/create-profile" 
              className="flex items-center gap-3 p-3 rounded-xl hover:bg-muted transition-colors"
              data-testid="nav-profile"
            >
              <Settings className="w-5 h-5" />
              <span>Edit Profile</span>
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
            {/* Header with Availability Toggle */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
              <div>
                <h1 className="font-heading text-2xl lg:text-3xl font-bold mb-2">
                  Welcome back, {user?.name?.split(' ')[0]}!
                </h1>
                <p className="text-muted-foreground">Manage your bookings and track your earnings.</p>
              </div>
              <div className="flex items-center gap-3 p-4 bg-card rounded-xl border border-border">
                <div className={`w-3 h-3 rounded-full ${availability ? 'bg-green-500' : 'bg-gray-400'}`} />
                <span className="font-medium">{availability ? 'Available' : 'Offline'}</span>
                <Switch 
                  checked={availability}
                  onCheckedChange={handleAvailabilityToggle}
                  data-testid="availability-toggle"
                />
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <Card className="border-border" data-testid="earnings-card">
                <CardContent className="p-6">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                      <DollarSign className="w-6 h-6 text-emerald-600" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Total Earnings</p>
                      <p className="text-2xl font-bold font-heading">
                        KSh {dashboardData?.total_earnings?.toLocaleString() || 0}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-border" data-testid="pending-card">
                <CardContent className="p-6">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center">
                      <Clock className="w-6 h-6 text-yellow-600" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Pending</p>
                      <p className="text-2xl font-bold font-heading">
                        KSh {dashboardData?.pending_earnings?.toLocaleString() || 0}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-border" data-testid="rating-card">
                <CardContent className="p-6">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                      <Star className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Rating</p>
                      <p className="text-2xl font-bold font-heading">
                        {dashboardData?.rating?.toFixed(1) || '0.0'}/5
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-border" data-testid="jobs-card">
                <CardContent className="p-6">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                      <TrendingUp className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Jobs Done</p>
                      <p className="text-2xl font-bold font-heading">
                        {dashboardData?.total_jobs || 0}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="grid lg:grid-cols-2 gap-6">
              {/* Upcoming Bookings */}
              <Card className="border-border" data-testid="upcoming-bookings">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="font-heading text-lg">Upcoming Bookings</CardTitle>
                  <Link to="/professional/bookings" className="text-primary text-sm hover:underline flex items-center gap-1">
                    View all <ChevronRight className="w-4 h-4" />
                  </Link>
                </CardHeader>
                <CardContent>
                  {dashboardData?.upcoming_bookings?.length > 0 ? (
                    <div className="space-y-4">
                      {dashboardData.upcoming_bookings.map((booking) => (
                        <div 
                          key={booking.id}
                          className="flex items-center justify-between p-4 bg-muted/50 rounded-xl"
                        >
                          <div className="flex items-center gap-4">
                            <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                              <User className="w-5 h-5 text-primary" />
                            </div>
                            <div>
                              <p className="font-medium">{booking.client?.name || "Client"}</p>
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
                      <p className="text-muted-foreground">No upcoming bookings</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Recent Reviews */}
              <Card className="border-border" data-testid="recent-reviews">
                <CardHeader>
                  <CardTitle className="font-heading text-lg">Recent Reviews</CardTitle>
                </CardHeader>
                <CardContent>
                  {dashboardData?.recent_reviews?.length > 0 ? (
                    <div className="space-y-4">
                      {dashboardData.recent_reviews.map((review) => (
                        <div key={review.id} className="p-4 bg-muted/50 rounded-xl">
                          <div className="flex items-center gap-2 mb-2">
                            <div className="flex items-center">
                              {[...Array(5)].map((_, i) => (
                                <Star 
                                  key={i}
                                  className={`w-4 h-4 ${i < review.rating ? 'text-primary fill-primary' : 'text-muted-foreground'}`}
                                />
                              ))}
                            </div>
                            <span className="text-sm text-muted-foreground">
                              {new Date(review.created_at).toLocaleDateString()}
                            </span>
                          </div>
                          <p className="text-sm">{review.comment}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Star className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                      <p className="text-muted-foreground">No reviews yet</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Commission Info */}
            <Card className="mt-6 border-border bg-secondary/5" data-testid="commission-info">
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-primary/20 rounded-xl flex items-center justify-center flex-shrink-0">
                    <AlertCircle className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-heading font-semibold mb-1">Platform Commission</h3>
                    <p className="text-sm text-muted-foreground">
                      Kazi Links charges a <strong>20% platform fee</strong> on each transaction. This covers payment processing, 
                      customer support, and platform maintenance. You receive <strong>80%</strong> of the agreed price after job completion.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>

      {/* Mobile Bottom Navigation */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 glass border-t border-border/40 px-6 py-3">
        <div className="flex items-center justify-around">
          <Link to="/professional" className="flex flex-col items-center gap-1 text-primary">
            <Home className="w-5 h-5" />
            <span className="text-xs">Home</span>
          </Link>
          <Link to="/professional/bookings" className="flex flex-col items-center gap-1 text-muted-foreground">
            <Calendar className="w-5 h-5" />
            <span className="text-xs">Bookings</span>
          </Link>
          <Link to="/create-profile" className="flex flex-col items-center gap-1 text-muted-foreground">
            <Settings className="w-5 h-5" />
            <span className="text-xs">Profile</span>
          </Link>
        </div>
      </nav>
    </div>
  );
}
