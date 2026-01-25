import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { 
  ArrowLeft, Send, Clock, CheckCircle2, XCircle, DollarSign,
  MapPin, User, Briefcase
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function MyBids() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [bids, setBids] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBids();
  }, []);

  const fetchBids = async () => {
    try {
      const response = await axios.get(`${API}/bids/my`);
      setBids(response.data);
    } catch (error) {
      console.error("Failed to fetch bids:", error);
      toast.error("Failed to load bids");
    } finally {
      setLoading(false);
    }
  };

  const statusColors = {
    pending: "bg-yellow-100 text-yellow-800",
    accepted: "bg-green-100 text-green-800",
    rejected: "bg-red-100 text-red-800"
  };

  const statusIcons = {
    pending: Clock,
    accepted: CheckCircle2,
    rejected: XCircle
  };

  const filterBids = (status) => {
    if (status === "all") return bids;
    return bids.filter(b => b.status === status);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-20 lg:pb-0" data-testid="my-bids-page">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-border/40">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-muted rounded-lg">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="font-heading font-semibold">My Bids</h1>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <Card className="border-border">
            <CardContent className="p-4 text-center">
              <Clock className="w-6 h-6 text-yellow-600 mx-auto mb-2" />
              <p className="text-2xl font-bold">{filterBids("pending").length}</p>
              <p className="text-xs text-muted-foreground">Pending</p>
            </CardContent>
          </Card>
          <Card className="border-border">
            <CardContent className="p-4 text-center">
              <CheckCircle2 className="w-6 h-6 text-green-600 mx-auto mb-2" />
              <p className="text-2xl font-bold">{filterBids("accepted").length}</p>
              <p className="text-xs text-muted-foreground">Accepted</p>
            </CardContent>
          </Card>
          <Card className="border-border">
            <CardContent className="p-4 text-center">
              <XCircle className="w-6 h-6 text-red-600 mx-auto mb-2" />
              <p className="text-2xl font-bold">{filterBids("rejected").length}</p>
              <p className="text-xs text-muted-foreground">Rejected</p>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="all" className="w-full">
          <TabsList className="w-full mb-6">
            <TabsTrigger value="all" className="flex-1">All ({bids.length})</TabsTrigger>
            <TabsTrigger value="pending" className="flex-1">Pending</TabsTrigger>
            <TabsTrigger value="accepted" className="flex-1">Accepted</TabsTrigger>
          </TabsList>

          {["all", "pending", "accepted", "rejected"].map((tab) => (
            <TabsContent key={tab} value={tab}>
              {filterBids(tab).length > 0 ? (
                <div className="space-y-4">
                  {filterBids(tab).map((bid) => {
                    const StatusIcon = statusIcons[bid.status];
                    return (
                      <Card key={bid.id} className="border-border" data-testid={`bid-${bid.id}`}>
                        <CardContent className="p-6">
                          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                            <div className="flex-1">
                              <div className="flex items-start gap-3 mb-3">
                                <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center flex-shrink-0">
                                  <Briefcase className="w-5 h-5 text-primary" />
                                </div>
                                <div>
                                  <h3 className="font-heading font-semibold">{bid.job?.title || "Job"}</h3>
                                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <User className="w-3 h-3" />
                                    <span>{bid.job?.client?.name || "Client"}</span>
                                  </div>
                                </div>
                              </div>
                              
                              <div className="pl-13 space-y-2">
                                <div className="flex flex-wrap items-center gap-4 text-sm">
                                  <div className="flex items-center gap-1">
                                    <MapPin className="w-4 h-4 text-muted-foreground" />
                                    <span>{bid.job?.location || "N/A"}</span>
                                  </div>
                                  <Badge variant="outline">{bid.job?.category}</Badge>
                                </div>
                                
                                <div className="p-3 bg-muted/50 rounded-lg">
                                  <p className="text-sm text-muted-foreground mb-2">Your message:</p>
                                  <p className="text-sm">{bid.message}</p>
                                </div>
                              </div>
                            </div>
                            
                            <div className="flex flex-col items-end gap-3">
                              <Badge className={statusColors[bid.status]}>
                                <StatusIcon className="w-3 h-3 mr-1" />
                                {bid.status.charAt(0).toUpperCase() + bid.status.slice(1)}
                              </Badge>
                              
                              <div className="text-right">
                                <p className="text-xs text-muted-foreground">Your Bid</p>
                                <p className="text-xl font-bold text-primary">
                                  KSh {bid.proposed_price.toLocaleString()}
                                </p>
                              </div>
                              
                              <div className="text-right text-sm text-muted-foreground">
                                <p>Client Budget</p>
                                <p>KSh {bid.job?.budget?.toLocaleString() || "N/A"}</p>
                              </div>
                              
                              {bid.status === "accepted" && (
                                <Button 
                                  onClick={() => navigate("/professional/bookings")}
                                  className="rounded-xl"
                                  data-testid={`view-booking-${bid.id}`}
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
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Send className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                  <h3 className="font-heading text-xl font-semibold mb-2">No bids yet</h3>
                  <p className="text-muted-foreground mb-6">
                    Start bidding on available jobs to grow your business
                  </p>
                  <Button onClick={() => navigate("/professional/jobs")} className="rounded-full">
                    Browse Jobs
                  </Button>
                </div>
              )}
            </TabsContent>
          ))}
        </Tabs>
      </main>
    </div>
  );
}
