import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { 
  ArrowLeft, Star, MapPin, Clock, DollarSign, User, 
  CheckCircle2, XCircle, Briefcase, MessageSquare, AlertCircle
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function JobBids() {
  const { jobId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [bids, setBids] = useState([]);
  const [loading, setLoading] = useState(true);
  const [acceptingBid, setAcceptingBid] = useState(null);
  const [selectedBid, setSelectedBid] = useState(null);

  useEffect(() => {
    fetchJobAndBids();
  }, [jobId]);

  const fetchJobAndBids = async () => {
    try {
      const [jobRes, bidsRes] = await Promise.all([
        axios.get(`${API}/jobs/${jobId}`),
        axios.get(`${API}/bids/job/${jobId}`)
      ]);
      setJob(jobRes.data);
      setBids(bidsRes.data);
    } catch (error) {
      console.error("Failed to fetch data:", error);
      toast.error("Failed to load job details");
      navigate("/client");
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptBid = async (bid) => {
    setAcceptingBid(bid.id);
    try {
      await axios.put(`${API}/bids/${bid.id}/accept`);
      toast.success("Bid accepted! A booking has been created.");
      navigate("/client/bookings");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to accept bid");
    } finally {
      setAcceptingBid(null);
    }
  };

  const handleRejectBid = async (bidId) => {
    try {
      await axios.put(`${API}/bids/${bidId}/reject`);
      toast.success("Bid rejected");
      fetchJobAndBids();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to reject bid");
    }
  };

  const statusColors = {
    pending: "bg-yellow-100 text-yellow-800",
    accepted: "bg-green-100 text-green-800",
    rejected: "bg-red-100 text-red-800"
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!job) return null;

  const pendingBids = bids.filter(b => b.status === "pending");
  const isJobOpen = job.status === "open";

  return (
    <div className="min-h-screen bg-background pb-20 lg:pb-0" data-testid="job-bids-page">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-border/40">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-muted rounded-lg">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="font-heading font-semibold">Bids for Job</h1>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6">
        {/* Job Summary */}
        <Card className="border-border mb-6" data-testid="job-summary">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center flex-shrink-0">
                <Briefcase className="w-6 h-6 text-primary" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <h2 className="font-heading text-xl font-bold">{job.title}</h2>
                  <Badge className={job.status === "open" ? "bg-green-100 text-green-800" : "bg-blue-100 text-blue-800"}>
                    {job.status}
                  </Badge>
                </div>
                <p className="text-muted-foreground mb-3">{job.description}</p>
                <div className="flex flex-wrap items-center gap-4 text-sm">
                  <div className="flex items-center gap-1">
                    <MapPin className="w-4 h-4 text-muted-foreground" />
                    <span>{job.location}</span>
                  </div>
                  <div className="flex items-center gap-1 text-primary font-semibold">
                    <DollarSign className="w-4 h-4" />
                    <span>Budget: KSh {job.budget.toLocaleString()}</span>
                  </div>
                  <Badge variant="outline">{job.category}</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Bids List */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-heading text-lg font-semibold">
            {pendingBids.length} Bid{pendingBids.length !== 1 ? 's' : ''} Received
          </h3>
        </div>

        {!isJobOpen && (
          <div className="p-4 bg-blue-50 rounded-xl mb-6 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-blue-900">Job is no longer accepting bids</p>
              <p className="text-sm text-blue-700">You have already accepted a bid for this job.</p>
            </div>
          </div>
        )}

        {bids.length > 0 ? (
          <div className="space-y-4">
            {bids.map((bid) => (
              <Card 
                key={bid.id} 
                className={`border-border ${bid.status !== "pending" ? "opacity-75" : ""}`}
                data-testid={`bid-card-${bid.id}`}
              >
                <CardContent className="p-6">
                  <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
                    <div className="flex items-start gap-4 flex-1">
                      <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center flex-shrink-0">
                        <User className="w-6 h-6 text-primary" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium">{bid.professional?.name}</h4>
                          {bid.profile?.rating > 0 && (
                            <div className="flex items-center gap-1 text-sm">
                              <Star className="w-4 h-4 text-primary fill-primary" />
                              <span>{bid.profile.rating.toFixed(1)}</span>
                            </div>
                          )}
                          <Badge className={statusColors[bid.status]}>
                            {bid.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mb-3">
                          {bid.profile?.profession} • {bid.profile?.experience_years || 0} years experience
                        </p>
                        
                        {/* Professional Stats */}
                        <div className="flex flex-wrap gap-4 mb-3 text-sm">
                          <span className="text-muted-foreground">
                            {bid.profile?.total_jobs || 0} jobs completed
                          </span>
                          <span className="text-muted-foreground">
                            {bid.profile?.total_reviews || 0} reviews
                          </span>
                        </div>
                        
                        {/* Bid Message */}
                        <div className="p-3 bg-muted/50 rounded-lg">
                          <div className="flex items-center gap-2 mb-2 text-sm text-muted-foreground">
                            <MessageSquare className="w-4 h-4" />
                            <span>Message from professional:</span>
                          </div>
                          <p className="text-sm">{bid.message}</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex flex-col items-end gap-3 min-w-[180px]">
                      <div className="text-right">
                        <p className="text-xs text-muted-foreground">Proposed Price</p>
                        <p className="text-2xl font-bold text-primary">
                          KSh {bid.proposed_price.toLocaleString()}
                        </p>
                        {bid.estimated_hours && (
                          <p className="text-sm text-muted-foreground">
                            Est. {bid.estimated_hours} hours
                          </p>
                        )}
                      </div>
                      
                      {bid.status === "pending" && isJobOpen && (
                        <div className="flex gap-2 w-full">
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button 
                                className="flex-1 rounded-xl gap-2"
                                onClick={() => setSelectedBid(bid)}
                                data-testid={`accept-bid-${bid.id}`}
                              >
                                <CheckCircle2 className="w-4 h-4" />
                                Accept
                              </Button>
                            </DialogTrigger>
                            <DialogContent>
                              <DialogHeader>
                                <DialogTitle>Accept This Bid?</DialogTitle>
                              </DialogHeader>
                              <div className="space-y-4 mt-4">
                                <div className="p-4 bg-muted/50 rounded-xl">
                                  <div className="flex justify-between mb-2">
                                    <span className="text-muted-foreground">Professional</span>
                                    <span className="font-medium">{bid.professional?.name}</span>
                                  </div>
                                  <div className="flex justify-between mb-2">
                                    <span className="text-muted-foreground">Agreed Price</span>
                                    <span className="font-bold">KSh {bid.proposed_price.toLocaleString()}</span>
                                  </div>
                                  <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Platform Fee (20%)</span>
                                    <span>KSh {(bid.proposed_price * 0.2).toLocaleString()}</span>
                                  </div>
                                </div>
                                
                                <div className="p-3 bg-primary/5 rounded-xl text-sm">
                                  <p>By accepting this bid:</p>
                                  <ul className="mt-2 space-y-1 text-muted-foreground">
                                    <li>• A booking will be created automatically</li>
                                    <li>• Other bids will be rejected</li>
                                    <li>• Payment will be held in escrow when you pay</li>
                                  </ul>
                                </div>
                                
                                <Button 
                                  className="w-full h-12 rounded-xl"
                                  onClick={() => handleAcceptBid(bid)}
                                  disabled={acceptingBid === bid.id}
                                  data-testid="confirm-accept-btn"
                                >
                                  {acceptingBid === bid.id ? "Accepting..." : "Confirm & Accept Bid"}
                                </Button>
                              </div>
                            </DialogContent>
                          </Dialog>
                          
                          <Button 
                            variant="outline"
                            className="rounded-xl"
                            onClick={() => handleRejectBid(bid.id)}
                            data-testid={`reject-bid-${bid.id}`}
                          >
                            <XCircle className="w-4 h-4" />
                          </Button>
                        </div>
                      )}
                      
                      {bid.status === "accepted" && (
                        <Button 
                          onClick={() => navigate("/client/bookings")}
                          className="w-full rounded-xl"
                        >
                          View Booking
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  <p className="text-xs text-muted-foreground mt-4 text-right">
                    Submitted {new Date(bid.created_at).toLocaleDateString()}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <MessageSquare className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="font-heading text-xl font-semibold mb-2">No bids yet</h3>
            <p className="text-muted-foreground">
              Professionals will submit their bids soon. Check back later!
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
