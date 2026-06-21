import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Calendar } from "../components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "../components/ui/popover";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { format } from "date-fns";
import { 
  ArrowLeft, Calendar as CalendarIcon, Clock, DollarSign, User, CheckCircle2, 
  XCircle, AlertCircle, CreditCard, Star, RefreshCw, Unlock, Loader2
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
  const [releasingPayment, setReleasingPayment] = useState(null);
  
  // Review state
  const [reviewOpen, setReviewOpen] = useState(false);
  const [reviewBooking, setReviewBooking] = useState(null);
  const [reviewData, setReviewData] = useState({ rating: 5, comment: "" });
  const [submittingReview, setSubmittingReview] = useState(false);
  
  // Rebook state
  const [rebookOpen, setRebookOpen] = useState(false);
  const [rebookBooking, setRebookBooking] = useState(null);
  const [rebookData, setRebookData] = useState({
    service_description: "",
    scheduled_date: null,
    estimated_hours: "",
    agreed_price: ""
  });
  const [submittingRebook, setSubmittingRebook] = useState(false);

  // Payment quote state — fetched when the user opens the Pay & Confirm dialog
  const [paymentQuote, setPaymentQuote] = useState(null);
  const [loadingQuote, setLoadingQuote] = useState(false);
  const [quoteBookingId, setQuoteBookingId] = useState(null);

  const fetchPaymentQuote = async (booking) => {
    setQuoteBookingId(booking.id);
    setLoadingQuote(true);
    setPaymentQuote(null);
    try {
      const res = await axios.get(`${API}/payments/quote?booking_id=${booking.id}`);
      setPaymentQuote(res.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not load payment quote");
    } finally {
      setLoadingQuote(false);
    }
  };

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
      const res = await axios.post(`${API}/payments/initiate`, {
        booking_id: booking.id,
      });
      if (res.data?.topup_required && res.data.topup_required > 0) {
        toast.success(
          `Check your phone for the M-Pesa prompt for KSh ${Number(res.data.topup_required).toLocaleString()}`,
          { duration: 6000 }
        );
      } else {
        toast.success("Payment held in escrow!");
      }
      fetchBookings();
      setSelectedBooking(null);
      setPaymentQuote(null);
      setQuoteBookingId(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Payment failed");
    } finally {
      setProcessingPayment(false);
    }
  };

  const handleReleasePayment = async (paymentId) => {
    setReleasingPayment(paymentId);
    try {
      await axios.post(`${API}/payments/${paymentId}/release`);
      toast.success("Payment released to professional!");
      fetchBookings();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to release payment");
    } finally {
      setReleasingPayment(null);
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

  const handleSubmitReview = async (e) => {
    e.preventDefault();
    if (!reviewBooking) return;
    
    setSubmittingReview(true);
    try {
      await axios.post(`${API}/reviews`, {
        booking_id: reviewBooking.id,
        professional_id: reviewBooking.professional_id,
        rating: reviewData.rating,
        comment: reviewData.comment
      });
      
      toast.success("Review submitted! Thank you for your feedback.");
      setReviewOpen(false);
      setReviewData({ rating: 5, comment: "" });
      fetchBookings();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to submit review");
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleRebook = async (e) => {
    e.preventDefault();
    if (!rebookBooking || !rebookData.scheduled_date) {
      toast.error("Please fill all required fields");
      return;
    }
    
    setSubmittingRebook(true);
    try {
      await axios.post(`${API}/bookings/rebook/${rebookBooking.professional_id}`, {
        professional_id: rebookBooking.professional_id,
        service_description: rebookData.service_description,
        scheduled_date: rebookData.scheduled_date.toISOString(),
        estimated_hours: rebookData.estimated_hours ? parseFloat(rebookData.estimated_hours) : null,
        agreed_price: parseFloat(rebookData.agreed_price)
      });
      
      toast.success("Booking created successfully!");
      setRebookOpen(false);
      setRebookData({ service_description: "", scheduled_date: null, estimated_hours: "", agreed_price: "" });
      fetchBookings();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create booking");
    } finally {
      setSubmittingRebook(false);
    }
  };

  const openReviewDialog = (booking) => {
    setReviewBooking(booking);
    setReviewData({ rating: 5, comment: "" });
    setReviewOpen(true);
  };

  const openRebookDialog = (booking) => {
    setRebookBooking(booking);
    setRebookData({
      service_description: booking.service_description,
      scheduled_date: null,
      estimated_hours: booking.estimated_hours?.toString() || "",
      agreed_price: booking.agreed_price?.toString() || ""
    });
    setRebookOpen(true);
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
                    const canReview = user.role === "client" && booking.status === "completed" && !booking.reviewed;
                    const canRebook = user.role === "client" && booking.status === "completed";
                    const canReleasePayment = user.role === "client" && booking.status === "completed" && booking.payment?.status === "escrow";
                    
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
                                    <CalendarIcon className="w-3 h-3" />
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
                              {booking.payment && (
                                <Badge variant="outline" className="text-xs">
                                  Payment: {booking.payment.status}
                                </Badge>
                              )}
                            </div>
                          </div>

                          {/* Actions */}
                          <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-border">
                            {/* Client: Pay for pending booking OR retry a stalled payment */}
                            {user.role === "client" && booking.status === "pending" && (() => {
                              const payStatus = booking.payment?.status;
                              const needsPayment = !booking.payment || payStatus === "awaiting_topup" || payStatus === "failed" || payStatus === "cancelled_retry";
                              if (!needsPayment) return null;
                              const isRetry = !!booking.payment;
                              return (
                              <Dialog
                                onOpenChange={(open) => {
                                  if (open) {
                                    setSelectedBooking(booking);
                                    fetchPaymentQuote(booking);
                                  } else {
                                    setPaymentQuote(null);
                                    setQuoteBookingId(null);
                                  }
                                }}
                              >
                                <DialogTrigger asChild>
                                  <Button
                                    className="rounded-xl gap-2"
                                    onClick={() => setSelectedBooking(booking)}
                                    data-testid={`pay-btn-${booking.id}`}
                                  >
                                    <CreditCard className="w-4 h-4" />
                                    {isRetry ? "Retry payment" : "Pay & Confirm"}
                                  </Button>
                                </DialogTrigger>
                                <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto">
                                  <DialogHeader>
                                    <DialogTitle>Confirm and Pay</DialogTitle>
                                  </DialogHeader>
                                  <div className="space-y-4 mt-2">
                                    {/* Service summary */}
                                    <div className="rounded-xl bg-muted/40 p-3">
                                      <p className="text-xs text-muted-foreground mb-0.5">Service</p>
                                      <p className="font-medium text-sm">{booking.service_description}</p>
                                    </div>

                                    {/* Loading or quote breakdown */}
                                    {loadingQuote || quoteBookingId !== booking.id || !paymentQuote ? (
                                      <div className="rounded-xl border border-border p-4 flex items-center gap-2 text-muted-foreground">
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        <span className="text-sm">Calculating total…</span>
                                      </div>
                                    ) : (
                                      <>
                                        {/* Charge breakdown */}
                                        <div className="rounded-xl border border-border p-4 space-y-2">
                                          <div className="flex justify-between text-sm">
                                            <span className="text-muted-foreground">Service amount</span>
                                            <span className="font-medium">KSh {Number(paymentQuote.service_amount).toLocaleString()}</span>
                                          </div>
                                          <div className="flex justify-between text-sm">
                                            <span className="text-muted-foreground">
                                              Platform fee ({paymentQuote.platform_fee_percent}%)
                                            </span>
                                            <span>KSh {Number(paymentQuote.platform_fee_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                                          </div>
                                          <div className="flex justify-between text-sm">
                                            <span className="text-muted-foreground">Fixed fee</span>
                                            <span>KSh {Number(paymentQuote.fixed_fee).toLocaleString()}</span>
                                          </div>
                                          <div className="flex justify-between pt-2 border-t border-border">
                                            <span className="font-medium">Total</span>
                                            <span className="font-bold text-lg" data-testid="payment-total">
                                              KSh {Number(paymentQuote.total).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                            </span>
                                          </div>
                                        </div>

                                        {/* Funding source */}
                                        <div className="rounded-xl bg-primary/5 p-3 space-y-1.5 text-sm">
                                          <div className="flex justify-between">
                                            <span className="text-muted-foreground">Your wallet</span>
                                            <span className="font-medium">KSh {Number(paymentQuote.wallet_balance).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                                          </div>
                                          <div className="flex justify-between">
                                            <span className="text-muted-foreground">From wallet</span>
                                            <span className="font-medium text-green-700">−KSh {Number(paymentQuote.wallet_used).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                                          </div>
                                          {paymentQuote.topup_required > 0 && (
                                            <div className="flex justify-between">
                                              <span className="text-muted-foreground">Pay via M-Pesa</span>
                                              <span className="font-semibold text-amber-700" data-testid="topup-required">
                                                KSh {Number(paymentQuote.topup_required).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                              </span>
                                            </div>
                                          )}
                                        </div>

                                        {paymentQuote.fully_covered_by_wallet ? (
                                          <div className="p-3 bg-green-50 rounded-xl text-sm flex items-center gap-2 text-green-800" data-testid="payment-mode-wallet">
                                            <CheckCircle2 className="w-4 h-4" />
                                            Your wallet covers this booking. Payment will move to escrow instantly.
                                          </div>
                                        ) : (
                                          <div className="p-3 bg-amber-50 rounded-xl text-sm flex items-center gap-2 text-amber-900" data-testid="payment-mode-mpesa">
                                            <AlertCircle className="w-4 h-4" />
                                            You'll receive an M-Pesa STK prompt for KSh{" "}
                                            {Number(paymentQuote.topup_required).toLocaleString(undefined, { minimumFractionDigits: 2 })}.
                                            Enter your PIN to release funds to escrow.
                                          </div>
                                        )}

                                        <Button
                                          className="w-full h-12 rounded-xl"
                                          onClick={() => handlePayment(booking)}
                                          disabled={processingPayment}
                                          data-testid="confirm-payment-btn"
                                        >
                                          {processingPayment
                                            ? "Processing…"
                                            : paymentQuote.fully_covered_by_wallet
                                              ? `Pay KSh ${Number(paymentQuote.total).toLocaleString(undefined, { minimumFractionDigits: 2 })} from wallet`
                                              : `Confirm & Pay KSh ${Number(paymentQuote.total).toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
                                        </Button>
                                      </>
                                    )}
                                  </div>
                                </DialogContent>
                              </Dialog>
                              );
                            })()}
                            
                            {/* Client: Release payment for completed booking */}
                            {canReleasePayment && (
                              <Button 
                                onClick={() => handleReleasePayment(booking.payment.id)}
                                disabled={releasingPayment === booking.payment.id}
                                className="rounded-xl gap-2 bg-green-600 hover:bg-green-700"
                                data-testid={`release-btn-${booking.id}`}
                              >
                                <Unlock className="w-4 h-4" />
                                {releasingPayment === booking.payment.id ? "Releasing..." : "Release Payment"}
                              </Button>
                            )}
                            
                            {/* Client: Rate professional */}
                            {canReview && (
                              <Button 
                                variant="outline"
                                onClick={() => openReviewDialog(booking)}
                                className="rounded-xl gap-2"
                                data-testid={`review-btn-${booking.id}`}
                              >
                                <Star className="w-4 h-4" />
                                Rate Service
                              </Button>
                            )}
                            
                            {/* Client: Rebook professional */}
                            {canRebook && (
                              <Button 
                                variant="outline"
                                onClick={() => openRebookDialog(booking)}
                                className="rounded-xl gap-2"
                                data-testid={`rebook-btn-${booking.id}`}
                              >
                                <RefreshCw className="w-4 h-4" />
                                Book Again
                              </Button>
                            )}
                            
                            {/* Professional: Start work */}
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
                            
                            {/* Professional: Mark complete */}
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
                            
                            {/* Cancel booking */}
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
                            
                            {/* Already reviewed badge */}
                            {user.role === "client" && booking.status === "completed" && booking.reviewed && (
                              <Badge variant="outline" className="gap-1">
                                <CheckCircle2 className="w-3 h-3" />
                                Reviewed
                              </Badge>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-12">
                  <CalendarIcon className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
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

      {/* Review Dialog */}
      <Dialog open={reviewOpen} onOpenChange={setReviewOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-heading">Rate Your Experience</DialogTitle>
          </DialogHeader>
          {reviewBooking && (
            <form onSubmit={handleSubmitReview} className="space-y-4 mt-4">
              <div className="p-4 bg-muted/50 rounded-xl text-center">
                <p className="text-sm text-muted-foreground mb-2">
                  How was your experience with {reviewBooking.professional?.name}?
                </p>
                <div className="flex justify-center gap-2 mb-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setReviewData({...reviewData, rating: star})}
                      className="focus:outline-none"
                      data-testid={`star-${star}`}
                    >
                      <Star 
                        className={`w-8 h-8 transition-colors ${
                          star <= reviewData.rating 
                            ? 'text-primary fill-primary' 
                            : 'text-muted-foreground'
                        }`}
                      />
                    </button>
                  ))}
                </div>
                <p className="text-sm font-medium">
                  {reviewData.rating === 5 && "Excellent!"}
                  {reviewData.rating === 4 && "Great!"}
                  {reviewData.rating === 3 && "Good"}
                  {reviewData.rating === 2 && "Fair"}
                  {reviewData.rating === 1 && "Poor"}
                </p>
              </div>
              
              <div className="space-y-2">
                <Label>Your Review (Optional)</Label>
                <Textarea
                  placeholder="Tell others about your experience..."
                  value={reviewData.comment}
                  onChange={(e) => setReviewData({...reviewData, comment: e.target.value})}
                  rows={4}
                  data-testid="review-comment"
                />
              </div>
              
              <Button 
                type="submit" 
                className="w-full h-12 rounded-xl"
                disabled={submittingReview}
                data-testid="submit-review-btn"
              >
                {submittingReview ? "Submitting..." : "Submit Review"}
              </Button>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Rebook Dialog */}
      <Dialog open={rebookOpen} onOpenChange={setRebookOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-heading">Book Again</DialogTitle>
          </DialogHeader>
          {rebookBooking && (
            <form onSubmit={handleRebook} className="space-y-4 mt-4">
              <div className="p-4 bg-muted/50 rounded-xl">
                <p className="text-sm text-muted-foreground">
                  Booking with <strong>{rebookBooking.professional?.name}</strong>
                </p>
              </div>
              
              <div className="space-y-2">
                <Label>Service Description</Label>
                <Textarea
                  placeholder="Describe what you need..."
                  value={rebookData.service_description}
                  onChange={(e) => setRebookData({...rebookData, service_description: e.target.value})}
                  required
                  data-testid="rebook-description"
                />
              </div>
              
              <div className="space-y-2">
                <Label>Preferred Date</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" className="w-full justify-start">
                      <CalendarIcon className="w-4 h-4 mr-2" />
                      {rebookData.scheduled_date 
                        ? format(rebookData.scheduled_date, "PPP")
                        : "Pick a date"
                      }
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0">
                    <Calendar
                      mode="single"
                      selected={rebookData.scheduled_date}
                      onSelect={(date) => setRebookData({...rebookData, scheduled_date: date})}
                      disabled={(date) => {
                        const today = new Date();
                        today.setHours(0, 0, 0, 0);
                        return date < today;
                      }}
                    />
                  </PopoverContent>
                </Popover>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Est. Hours</Label>
                  <Input
                    type="number"
                    placeholder="e.g., 2"
                    value={rebookData.estimated_hours}
                    onChange={(e) => setRebookData({...rebookData, estimated_hours: e.target.value})}
                    data-testid="rebook-hours"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Price (KSh)</Label>
                  <Input
                    type="number"
                    placeholder="e.g., 2500"
                    value={rebookData.agreed_price}
                    onChange={(e) => setRebookData({...rebookData, agreed_price: e.target.value})}
                    required
                    data-testid="rebook-price"
                  />
                </div>
              </div>
              
              <Button 
                type="submit" 
                className="w-full h-12 rounded-xl"
                disabled={submittingRebook}
                data-testid="submit-rebook-btn"
              >
                {submittingRebook ? "Creating Booking..." : "Confirm Booking"}
              </Button>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
