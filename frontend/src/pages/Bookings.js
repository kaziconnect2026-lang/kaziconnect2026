import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { 
  ArrowLeft, Calendar, Clock, DollarSign, User, CheckCircle2, 
  XCircle, AlertCircle, CreditCard
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Bookings() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [processingPayment, setProcessingPayment] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(null);

  useEffect(() => {
    fetchBookings();
  }, []);

  const fetchBookings = async () => {
    try {
      const response = await axios.get(`${API}/bookings`);
      setBookings(response.data);
    } catch (error) {
      console.error("Failed to fetch bookings:", error);
      toast.error("Failed to load bookings");
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async (booking) => {
    setProcessingPayment(true);
    try {
      const response = await axios.post(`${API}/payments/initiate`, {
        booking_id: booking.id,
        phone_number: user.phone || "254712345678"
      });
      
      toast.success("Payment held in escrow!");
      fetchBookings();
      setSelectedBooking(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Payment failed");
    } finally {
      setProcessingPayment(false);
    }
  };

  const handleStatusUpdate = async (bookingId, newStatus) => {
    setUpdatingStatus(bookingId);
    try {
      await axios.put(`${API}/bookings/${bookingId}/status?status=${newStatus}`);
      toast.success(`Booking ${newStatus.replace('_', ' ')}`);
      fetchBookings();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to update status");
    } finally {
      setUpdatingStatus(null);
    }
  };

  const statusColors = {
    pending: "bg-yellow-100 text-yellow-800",
    confirmed: "bg-blue-100 text-blue-800",
    in_progress: "bg-purple-100 text-purple-800",
    completed: "bg-green-100 text-green-800",
    cancelled: "bg-red-100 text-red-800"
  };

  const statusIcons = {
    pending: AlertCircle,
    confirmed: CheckCircle2,
    in_progress: Clock,
    completed: CheckCircle2,
    cancelled: XCircle
  };

  const filterBookings = (status) => {
    if (status === "all") return bookings;
    if (status === "active") return bookings.filter(b => ["pending", "confirmed", "in_progress"].includes(b.status));
    return bookings.filter(b => b.status === status);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-20 lg:pb-0" data-testid="bookings-page">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-border/40">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-muted rounded-lg">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="font-heading font-semibold">My Bookings</h1>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6">
        <Tabs defaultValue="all" className="w-full">
          <TabsList className="w-full mb-6">
            <TabsTrigger value="all" className="flex-1">All</TabsTrigger>
            <TabsTrigger value="active" className="flex-1">Active</TabsTrigger>
            <TabsTrigger value="completed" className="flex-1">Completed</TabsTrigger>
          </TabsList>

          {["all", "active", "completed"].map((tab) => (
            <TabsContent key={tab} value={tab}>
              {filterBookings(tab).length > 0 ? (
                <div className="space-y-4">
                  {filterBookings(tab).map((booking) => {
                    const StatusIcon = statusIcons[booking.status];
                    const otherParty = user.role === "client" ? booking.professional : booking.client;
                    
                    return (
                      <Card key={booking.id} className="border-border" data-testid={`booking-${booking.id}`}>
                        <CardContent className="p-6">
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                            <div className="flex items-start gap-4">
                              <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                                <User className="w-6 h-6 text-primary" />
                              </div>
                              <div>
                                <h3 className="font-medium">{otherParty?.name || "User"}</h3>
                                <p className="text-sm text-muted-foreground line-clamp-2">
                                  {booking.service_description}
                                </p>
                                <div className="flex flex-wrap items-center gap-3 mt-2">
                                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                                    <Calendar className="w-3 h-3" />
                                    {new Date(booking.scheduled_date).toLocaleDateString()}
                                  </span>
                                  {booking.estimated_hours && (
                                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                                      <Clock className="w-3 h-3" />
                                      {booking.estimated_hours} hrs
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                            
                            <div className="flex flex-col items-end gap-2">
                              <Badge className={statusColors[booking.status]}>
                                <StatusIcon className="w-3 h-3 mr-1" />
                                {booking.status.replace('_', ' ')}
                              </Badge>
                              <p className="text-lg font-bold">
                                KSh {booking.agreed_price.toLocaleString()}
                              </p>
                            </div>
                          </div>

                          {/* Actions */}
                          <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-border">
                            {user.role === "client" && booking.status === "pending" && (
                              <Dialog>
                                <DialogTrigger asChild>
                                  <Button 
                                    className="rounded-xl gap-2"
                                    onClick={() => setSelectedBooking(booking)}
                                    data-testid={`pay-btn-${booking.id}`}
                                  >
                                    <CreditCard className="w-4 h-4" />
                                    Pay & Confirm
                                  </Button>
                                </DialogTrigger>
                                <DialogContent>
                                  <DialogHeader>
                                    <DialogTitle>Confirm Payment</DialogTitle>
                                  </DialogHeader>
                                  <div className="space-y-4 mt-4">
                                    <div className="p-4 bg-muted/50 rounded-xl space-y-2">
                                      <div className="flex justify-between">
                                        <span className="text-muted-foreground">Service</span>
                                        <span className="font-medium">{booking.service_description}</span>
                                      </div>
                                      <div className="flex justify-between">
                                        <span className="text-muted-foreground">Amount</span>
                                        <span className="font-bold">KSh {booking.agreed_price.toLocaleString()}</span>
                                      </div>
                                      <div className="flex justify-between text-sm">
                                        <span className="text-muted-foreground">Platform Fee (20%)</span>
                                        <span>KSh {(booking.agreed_price * 0.2).toLocaleString()}</span>
                                      </div>
                                    </div>
                                    
                                    <div className="p-3 bg-primary/5 rounded-xl text-sm">
                                      <p className="flex items-center gap-2">
                                        <CheckCircle2 className="w-4 h-4 text-primary" />
                                        Payment will be held in escrow until job completion
                                      </p>
                                    </div>
                                    
                                    <p className="text-sm text-muted-foreground text-center">
                                      (M-Pesa payment is MOCKED for demo)
                                    </p>
                                    
                                    <Button 
                                      className="w-full h-12 rounded-xl"
                                      onClick={() => handlePayment(booking)}
                                      disabled={processingPayment}
                                      data-testid="confirm-payment-btn"
                                    >
                                      {processingPayment ? "Processing..." : "Confirm Payment"}
                                    </Button>
                                  </div>
                                </DialogContent>
                              </Dialog>
                            )}
                            
                            {user.role === "professional" && booking.status === "confirmed" && (
                              <Button 
                                onClick={() => handleStatusUpdate(booking.id, "in_progress")}
                                disabled={updatingStatus === booking.id}
                                className="rounded-xl"
                                data-testid={`start-btn-${booking.id}`}
                              >
                                Start Work
                              </Button>
                            )}
                            
                            {user.role === "professional" && booking.status === "in_progress" && (
                              <Button 
                                onClick={() => handleStatusUpdate(booking.id, "completed")}
                                disabled={updatingStatus === booking.id}
                                className="rounded-xl bg-green-600 hover:bg-green-700"
                                data-testid={`complete-btn-${booking.id}`}
                              >
                                Mark Complete
                              </Button>
                            )}
                            
                            {booking.status === "pending" && (
                              <Button 
                                variant="outline"
                                onClick={() => handleStatusUpdate(booking.id, "cancelled")}
                                disabled={updatingStatus === booking.id}
                                className="rounded-xl text-destructive"
                                data-testid={`cancel-btn-${booking.id}`}
                              >
                                Cancel
                              </Button>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Calendar className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                  <h3 className="font-heading text-xl font-semibold mb-2">No bookings found</h3>
                  <p className="text-muted-foreground mb-6">
                    {user.role === "client" 
                      ? "Find a professional to book your first service"
                      : "Complete your profile to start receiving bookings"
                    }
                  </p>
                  {user.role === "client" && (
                    <Button onClick={() => navigate("/search")} className="rounded-full">
                      Find Professionals
                    </Button>
                  )}
                </div>
              )}
            </TabsContent>
          ))}
        </Tabs>
      </main>
    </div>
  );
}
