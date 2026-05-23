import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Calendar } from "../components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "../components/ui/popover";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { format } from "date-fns";
import { 
  ArrowLeft, Star, MapPin, Clock, DollarSign, Briefcase,
  Phone, Mail, Calendar as CalendarIcon, CheckCircle2, Shield, MessageCircle, QrCode
} from "lucide-react";
import ShareProfileQRDialog from "../components/ShareProfileQRDialog";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ProfessionalProfile() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [professional, setProfessional] = useState(null);
  const [loading, setLoading] = useState(true);
  const [bookingOpen, setBookingOpen] = useState(false);
  const [bookingData, setBookingData] = useState({
    service_description: "",
    scheduled_date: null,
    estimated_hours: "",
    agreed_price: ""
  });
  const [submitting, setSubmitting] = useState(false);
  const [startingChat, setStartingChat] = useState(false);
  const [qrOpen, setQrOpen] = useState(false);

  const handleStartChat = async () => {
    if (startingChat) return;
    setStartingChat(true);
    try {
      const res = await axios.post(`${API}/conversations`, { other_user_id: id });
      navigate(`/messages/${res.data.id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to start conversation");
    } finally {
      setStartingChat(false);
    }
  };

  useEffect(() => {
    const fetchProfessional = async () => {
      try {
        const response = await axios.get(`${API}/professionals/${id}`);
        setProfessional(response.data);
      } catch (error) {
        console.error("Failed to fetch professional:", error);
        toast.error("Professional not found");
        navigate("/search");
      } finally {
        setLoading(false);
      }
    };
    fetchProfessional();
  }, [id, navigate]);

  const handleBooking = async (e) => {
    e.preventDefault();
    if (!bookingData.scheduled_date) {
      toast.error("Please select a date");
      return;
    }
    
    setSubmitting(true);
    try {
      const response = await axios.post(`${API}/bookings`, {
        professional_id: id,
        service_description: bookingData.service_description,
        scheduled_date: bookingData.scheduled_date.toISOString(),
        estimated_hours: parseFloat(bookingData.estimated_hours) || null,
        agreed_price: parseFloat(bookingData.agreed_price)
      });
      
      toast.success("Booking request sent!");
      setBookingOpen(false);
      navigate("/client/bookings");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create booking");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!professional) return null;

  return (
    <div className="min-h-screen bg-background" data-testid="professional-profile-page">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-border/40">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-muted rounded-lg">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="font-heading font-semibold flex-1">Professional Profile</h1>
          <button
            onClick={() => setQrOpen(true)}
            className="p-2 hover:bg-primary/10 rounded-lg text-primary"
            aria-label="Share profile QR code"
            data-testid="header-share-qr-btn"
          >
            <QrCode className="w-5 h-5" />
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6">
        {/* Profile Header */}
        <Card className="border-border mb-6 overflow-hidden" data-testid="profile-header">
          <div className="h-32 bg-gradient-to-br from-primary/30 to-accent/30" />
          <CardContent className="relative pt-0">
            <div className="flex flex-col sm:flex-row sm:items-end gap-4 -mt-12">
              <div className="w-24 h-24 bg-card border-4 border-background rounded-2xl flex items-center justify-center">
                <span className="text-3xl font-bold text-primary">
                  {professional.user?.name?.charAt(0) || "P"}
                </span>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h2 className="font-heading text-2xl font-bold">{professional.user?.name}</h2>
                  {professional.availability && (
                    <Badge className="bg-green-100 text-green-800">Available</Badge>
                  )}
                </div>
                <p className="text-muted-foreground">{professional.profession}</p>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1 bg-primary/10 px-3 py-2 rounded-xl">
                  <Star className="w-5 h-5 text-primary fill-primary" />
                  <span className="font-bold">{professional.rating?.toFixed(1) || "New"}</span>
                  <span className="text-sm text-muted-foreground">({professional.total_reviews} reviews)</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* About */}
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="font-heading">About</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">{professional.bio || "No bio provided"}</p>
                
                <div className="flex flex-wrap gap-2 mt-4">
                  {professional.skills?.map((skill, i) => (
                    <Badge key={i} variant="outline">{skill}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
              <Card className="border-border">
                <CardContent className="p-4 text-center">
                  <Briefcase className="w-6 h-6 text-primary mx-auto mb-2" />
                  <p className="text-2xl font-bold">{professional.total_jobs}</p>
                  <p className="text-xs text-muted-foreground">Jobs Completed</p>
                </CardContent>
              </Card>
              <Card className="border-border">
                <CardContent className="p-4 text-center">
                  <Clock className="w-6 h-6 text-primary mx-auto mb-2" />
                  <p className="text-2xl font-bold">{professional.experience_years}</p>
                  <p className="text-xs text-muted-foreground">Years Experience</p>
                </CardContent>
              </Card>
              <Card className="border-border">
                <CardContent className="p-4 text-center">
                  <Star className="w-6 h-6 text-primary mx-auto mb-2" />
                  <p className="text-2xl font-bold">{professional.total_reviews}</p>
                  <p className="text-xs text-muted-foreground">Reviews</p>
                </CardContent>
              </Card>
            </div>

            {/* Reviews */}
            <Card className="border-border" data-testid="reviews-section">
              <CardHeader>
                <CardTitle className="font-heading">Reviews</CardTitle>
              </CardHeader>
              <CardContent>
                {professional.reviews?.length > 0 ? (
                  <div className="space-y-4">
                    {professional.reviews.map((review) => (
                      <div key={review.id} className="p-4 bg-muted/50 rounded-xl">
                        <div className="flex items-center gap-2 mb-2">
                          <div className="flex">
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
                        <p className="text-xs text-muted-foreground mt-2">- {review.client_name}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-center py-8">No reviews yet</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Pricing Card */}
            <Card className="border-border sticky top-24" data-testid="pricing-card">
              <CardHeader>
                <CardTitle className="font-heading">Pricing</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {professional.hourly_rate && (
                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-xl">
                    <span className="text-muted-foreground">Hourly Rate</span>
                    <span className="font-bold text-lg">KSh {professional.hourly_rate.toLocaleString()}</span>
                  </div>
                )}
                {professional.project_rate_min && (
                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-xl">
                    <span className="text-muted-foreground">Project Rate</span>
                    <span className="font-bold text-lg">
                      KSh {professional.project_rate_min.toLocaleString()} - {professional.project_rate_max?.toLocaleString()}
                    </span>
                  </div>
                )}
                
                <div className="flex items-center gap-2 text-sm text-muted-foreground p-3 bg-primary/5 rounded-xl">
                  <Shield className="w-4 h-4 text-primary" />
                  <span>Secure M-Pesa escrow payment</span>
                </div>

                <Button
                  variant="outline"
                  className="w-full h-12 rounded-xl"
                  onClick={handleStartChat}
                  disabled={startingChat}
                  data-testid="message-pro-btn"
                >
                  <MessageCircle className="w-4 h-4 mr-2" />
                  {startingChat ? "Opening chat..." : "Message"}
                </Button>

                <Dialog open={bookingOpen} onOpenChange={setBookingOpen}>
                  <DialogTrigger asChild>
                    <Button 
                      className="w-full h-12 rounded-xl bg-primary hover:bg-primary/90"
                      data-testid="book-now-btn"
                    >
                      Book Now
                    </Button>
                  </DialogTrigger><DialogContent className="sm:max-w-md">
                    <DialogHeader>
                      <DialogTitle className="font-heading">Book {professional.user?.name}</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleBooking} className="space-y-4 mt-4">
                      <div className="space-y-2">
                        <Label>Service Description</Label>
                        <Textarea
                          placeholder="Describe what you need..."
                          value={bookingData.service_description}
                          onChange={(e) => setBookingData({...bookingData, service_description: e.target.value})}
                          required
                          data-testid="booking-description"
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <Label>Preferred Date</Label>
                        <Popover>
                          <PopoverTrigger asChild>
                            <Button variant="outline" className="w-full justify-start">
                              <CalendarIcon className="w-4 h-4 mr-2" />
                              {bookingData.scheduled_date 
                                ? format(bookingData.scheduled_date, "PPP")
                                : "Pick a date"
                              }
                            </Button>
                          </PopoverTrigger>
                          <PopoverContent className="w-auto p-0">
                            <Calendar
                              mode="single"
                              selected={bookingData.scheduled_date}
                              onSelect={(date) => setBookingData({...bookingData, scheduled_date: date})}
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
                          <Label>Estimated Hours</Label>
                          <Input
                            type="number"
                            placeholder="e.g., 2"
                            value={bookingData.estimated_hours}
                            onChange={(e) => setBookingData({...bookingData, estimated_hours: e.target.value})}
                            data-testid="booking-hours"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Agreed Price (KSh)</Label>
                          <Input
                            type="number"
                            placeholder="e.g., 2500"
                            value={bookingData.agreed_price}
                            onChange={(e) => setBookingData({...bookingData, agreed_price: e.target.value})}
                            required
                            data-testid="booking-price"
                          />
                        </div>
                      </div>
                      
                      <div className="p-3 bg-primary/5 rounded-xl text-sm">
                        <p className="flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-primary" />
                          Payment held in escrow until job completion
                        </p>
                      </div>
                      
                      <Button 
                        type="submit" 
                        className="w-full h-12 rounded-xl"
                        disabled={submitting}
                        data-testid="confirm-booking-btn"
                      >
                        {submitting ? "Sending Request..." : "Confirm Booking"}
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>

                {/* Contact Info */}
                <div className="pt-4 border-t border-border space-y-3">
                  <div className="flex items-center gap-3 text-sm">
                    <MapPin className="w-4 h-4 text-muted-foreground" />
                    <span>{professional.user?.location || "Location not specified"}</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <Phone className="w-4 h-4 text-muted-foreground" />
                    {professional.phone_visible && professional.user?.phone ? (
                      <a
                        href={`tel:${professional.user.phone}`}
                        className="text-primary hover:underline"
                        data-testid="pro-phone"
                      >
                        {professional.user.phone}
                      </a>
                    ) : (
                      <span
                        className="text-muted-foreground italic"
                        data-testid="pro-phone-hidden"
                      >
                        Hidden — visible after booking is confirmed
                      </span>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      <ShareProfileQRDialog
        open={qrOpen}
        onOpenChange={setQrOpen}
        userId={id}
        name={professional.user?.name}
        profession={professional.profession}
        rating={professional.rating}
        totalJobs={professional.total_jobs}
      />
    </div>
  );
}
