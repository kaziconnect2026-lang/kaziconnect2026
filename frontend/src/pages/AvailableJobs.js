import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Textarea } from "../components/ui/textarea";
import { Label } from "../components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { 
  ArrowLeft, MapPin, DollarSign, Clock, User, 
  Briefcase, Send, CheckCircle2, Sparkles, Loader2, Wand2
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AvailableJobs() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [profession, setProfession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState(null);
  const [bidOpen, setBidOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [loadingAiSuggestion, setLoadingAiSuggestion] = useState(false);
  const [bidData, setBidData] = useState({
    proposed_price: "",
    message: "",
    estimated_hours: ""
  });

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/jobs/available`);
      // Handle new response format
      if (response.data.jobs) {
        setJobs(response.data.jobs);
        setProfession(response.data.profession);
      } else {
        // Fallback for old format
        setJobs(Array.isArray(response.data) ? response.data : []);
      }
    } catch (error) {
      console.error("Failed to fetch jobs:", error);
      toast.error("Failed to load jobs");
    } finally {
      setLoading(false);
    }
  };

  const handleGetAiSuggestion = async (job) => {
    setLoadingAiSuggestion(true);
    try {
      const response = await axios.post(`${API}/bids/ai-suggest?job_id=${job.id}`);
      setBidData({
        proposed_price: response.data.suggested_price?.toString() || job.budget.toString(),
        message: response.data.suggested_message || "",
        estimated_hours: response.data.suggested_hours?.toString() || ""
      });
      if (response.data.ai_powered) {
        toast.success("AI suggestion generated!");
      } else {
        toast.info("Generated basic suggestion");
      }
    } catch (error) {
      console.error("Failed to get AI suggestion:", error);
      toast.error("Failed to get AI suggestion");
      // Set default values
      setBidData({
        proposed_price: job.budget.toString(),
        message: "",
        estimated_hours: ""
      });
    } finally {
      setLoadingAiSuggestion(false);
    }
  };

  const handleSubmitBid = async (e) => {
    e.preventDefault();
    if (!selectedJob) return;
    
    setSubmitting(true);
    try {
      await axios.post(`${API}/bids`, {
        job_id: selectedJob.id,
        proposed_price: parseFloat(bidData.proposed_price),
        message: bidData.message,
        estimated_hours: bidData.estimated_hours ? parseFloat(bidData.estimated_hours) : null
      });
      
      toast.success("Bid submitted successfully!");
      setBidOpen(false);
      setBidData({ proposed_price: "", message: "", estimated_hours: "" });
      
      // Refresh jobs list
      fetchJobs();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to submit bid");
    } finally {
      setSubmitting(false);
    }
  };

  const openBidDialog = (job) => {
    setSelectedJob(job);
    setBidData({
      proposed_price: job.budget.toString(),
      message: "",
      estimated_hours: ""
    });
    setBidOpen(true);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-20 lg:pb-0" data-testid="available-jobs-page">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-border/40">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-muted rounded-lg">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="font-heading font-semibold">Available Jobs</h1>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6">
        {/* Category Info */}
        <div className="flex items-center gap-2 mb-6 p-4 bg-primary/5 rounded-xl">
          <Briefcase className="w-5 h-5 text-primary" />
          <span className="font-medium">
            {jobs.length} {profession ? `${profession}` : ""} job{jobs.length !== 1 ? 's' : ''} available
          </span>
          {profession && (
            <Badge className="ml-2 bg-primary/20 text-primary">
              Filtered by your profession
            </Badge>
          )}
        </div>

        {!profession && jobs.length === 0 && (
          <Card className="border-border mb-6 bg-yellow-50">
            <CardContent className="p-4">
              <p className="text-yellow-800 text-sm">
                <strong>Tip:</strong> Complete your profile with your profession to see jobs matching your skills.
              </p>
              <Button 
                variant="outline" 
                className="mt-2"
                onClick={() => navigate("/create-profile")}
              >
                Complete Profile
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Jobs List */}
        {jobs.length > 0 ? (
          <div className="space-y-4">
            {jobs.map((job) => (
              <Card 
                key={job.id} 
                className={`border-border transition-all ${job.has_bid ? 'opacity-75' : 'hover:shadow-card-hover'}`}
                data-testid={`job-card-${job.id}`}
              >
                <CardContent className="p-6">
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-start gap-3 mb-3">
                        <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center flex-shrink-0">
                          <Briefcase className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                          <h3 className="font-heading font-semibold text-lg">{job.title}</h3>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <User className="w-3 h-3" />
                            <span>{job.client?.name || "Client"}</span>
                            <span>•</span>
                            <span>{new Date(job.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>
                      
                      <p className="text-muted-foreground mb-4 line-clamp-2">{job.description}</p>
                      
                      <div className="flex flex-wrap items-center gap-4 text-sm">
                        <div className="flex items-center gap-1">
                          <MapPin className="w-4 h-4 text-muted-foreground" />
                          <span>{job.location}</span>
                        </div>
                        <div className="flex items-center gap-1 text-primary font-semibold">
                          <DollarSign className="w-4 h-4" />
                          <span>KSh {job.budget.toLocaleString()}</span>
                        </div>
                        <Badge variant="outline">{job.category}</Badge>
                        <span className="text-muted-foreground">
                          {job.bid_count} bid{job.bid_count !== 1 ? 's' : ''}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex flex-col items-end gap-2">
                      {job.has_bid ? (
                        <Badge className="bg-green-100 text-green-800">
                          <CheckCircle2 className="w-3 h-3 mr-1" />
                          Bid Submitted
                        </Badge>
                      ) : (
                        <Button 
                          onClick={() => openBidDialog(job)}
                          className="rounded-xl gap-2"
                          data-testid={`bid-btn-${job.id}`}
                        >
                          <Send className="w-4 h-4" />
                          Submit Bid
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <Briefcase className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="font-heading text-xl font-semibold mb-2">No jobs available</h3>
            <p className="text-muted-foreground mb-2">
              {profession 
                ? `No ${profession.toLowerCase()} jobs available right now.`
                : "Complete your profile to see jobs matching your skills."
              }
            </p>
            <p className="text-sm text-muted-foreground">
              Check back later for new job postings!
            </p>
          </div>
        )}
      </main>

      {/* Bid Dialog */}
      <Dialog open={bidOpen} onOpenChange={setBidOpen}>
        <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto p-5">
          <DialogHeader>
            <DialogTitle className="font-heading">Submit Your Bid</DialogTitle>
          </DialogHeader>
          {selectedJob && (
            <form onSubmit={handleSubmitBid} className="space-y-4 mt-4">
              <div className="p-4 bg-muted/50 rounded-xl mb-4">
                <h4 className="font-medium mb-1">{selectedJob.title}</h4>
                <p className="text-sm text-muted-foreground">Client Budget: KSh {selectedJob.budget.toLocaleString()}</p>
              </div>
              
              {/* AI Suggestion Button */}
              <Button
                type="button"
                variant="outline"
                className="w-full gap-2"
                onClick={() => handleGetAiSuggestion(selectedJob)}
                disabled={loadingAiSuggestion}
                data-testid="ai-suggest-btn"
              >
                {loadingAiSuggestion ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Generating suggestion...
                  </>
                ) : (
                  <>
                    <Wand2 className="w-4 h-4" />
                    Get AI Bid Suggestion
                  </>
                )}
              </Button>
              
              <div className="space-y-2">
                <Label>Your Proposed Price (KSh)</Label>
                <Input
                  type="number"
                  placeholder="Enter your price"
                  value={bidData.proposed_price}
                  onChange={(e) => setBidData({...bidData, proposed_price: e.target.value})}
                  required
                  className="h-12"
                  data-testid="bid-price-input"
                />
              </div>
              
              <div className="space-y-2">
                <Label>Estimated Hours (Optional)</Label>
                <Input
                  type="number"
                  placeholder="e.g., 4"
                  value={bidData.estimated_hours}
                  onChange={(e) => setBidData({...bidData, estimated_hours: e.target.value})}
                  className="h-12"
                  data-testid="bid-hours-input"
                />
              </div>
              
              <div className="space-y-2">
                <Label>Message to Client</Label>
                <Textarea
                  placeholder="Introduce yourself and explain why you're the best fit for this job..."
                  value={bidData.message}
                  onChange={(e) => setBidData({...bidData, message: e.target.value})}
                  required
                  rows={4}
                  data-testid="bid-message-input"
                />
              </div>
              
              <div className="p-3 bg-primary/5 rounded-xl text-sm">
                <p className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-primary" />
                  Tip: Use AI suggestion for a competitive bid!
                </p>
              </div>
              
              <Button 
                type="submit" 
                className="w-full h-12 rounded-xl"
                disabled={submitting}
                data-testid="submit-bid-btn"
              >
                {submitting ? "Submitting..." : "Submit Bid"}
              </Button>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
