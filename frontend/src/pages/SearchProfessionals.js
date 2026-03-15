import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { 
  Search, Star, MapPin, ArrowLeft, Filter, Clock, DollarSign,
  Sparkles, Zap, Scissors, Droplet, PenTool, Wrench, Paintbrush, Hammer
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const categoryIcons = {
  barber: Scissors,
  electrician: Zap,
  plumber: Droplet,
  tattoo_artist: PenTool,
  mechanic: Wrench,
  painter: Paintbrush,
  carpenter: Hammer,
  cleaner: Sparkles,
};

export default function SearchProfessionals() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState(searchParams.get("q") || "");
  const [selectedCategory, setSelectedCategory] = useState(searchParams.get("category") || "");
  const [professionals, setProfessionals] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [aiMatching, setAiMatching] = useState(false);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await axios.get(`${API}/categories/grouped`);
        setCategories(response.data);
      } catch (error) {
        console.error("Failed to fetch categories:", error);
      }
    };
    fetchCategories();
  }, []);

  useEffect(() => {
    const fetchProfessionals = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (selectedCategory) params.append("category", selectedCategory);
        
        const response = await axios.get(`${API}/professionals/search?${params.toString()}`);
        setProfessionals(response.data);
      } catch (error) {
        console.error("Failed to fetch professionals:", error);
        toast.error("Failed to load professionals");
      } finally {
        setLoading(false);
      }
    };
    fetchProfessionals();
  }, [selectedCategory]);

  const handleAIMatch = async () => {
    if (!searchQuery) {
      toast.error("Please describe what you need");
      return;
    }
    
    setAiMatching(true);
    try {
      const response = await axios.post(`${API}/match`, {
        job_description: searchQuery,
        category: selectedCategory || "general",
        location: user?.location || "Nairobi",
        budget: 5000,
      });
      
      setProfessionals(response.data.matches);
      if (response.data.ai_powered) {
        toast.success("AI-powered matches found!");
      }
    } catch (error) {
      console.error("AI matching failed:", error);
      toast.error("AI matching failed, showing regular results");
    } finally {
      setAiMatching(false);
    }
  };

  const handleCategoryChange = (value) => {
    setSelectedCategory(value === "all" ? "" : value);
    setSearchParams(value === "all" ? {} : { category: value });
  };

  return (
    <div className="min-h-screen bg-background" data-testid="search-page">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-border/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4 h-16">
            <button onClick={() => navigate(-1)} className="p-2 hover:bg-muted rounded-lg">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="flex-1 flex items-center gap-3">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="What service do you need?"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 h-11 rounded-xl"
                  data-testid="search-input"
                />
              </div>
              <Button 
                onClick={handleAIMatch}
                disabled={aiMatching}
                className="rounded-xl bg-primary hover:bg-primary/90 gap-2"
                data-testid="ai-match-btn"
              >
                <Sparkles className="w-4 h-4" />
                {aiMatching ? "Matching..." : "AI Match"}
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4 mb-6">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium">Filter by:</span>
          </div>
          <Select value={selectedCategory || "all"} onValueChange={handleCategoryChange}>
            <SelectTrigger className="w-48 rounded-xl" data-testid="category-filter">
              <SelectValue placeholder="All Categories" />
            </SelectTrigger>
            <SelectContent className="max-h-80">
              <SelectItem value="all">All Categories</SelectItem>
              {Object.entries(categories).map(([groupName, groupCats]) => (
                <div key={groupName}>
                  <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground bg-muted/50 sticky top-0">
                    {groupName}
                  </div>
                  {groupCats.map((cat) => (
                    <SelectItem key={cat.id} value={cat.id}>{cat.name}</SelectItem>
                  ))}
                </div>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Category Pills */}
        <div className="flex flex-wrap gap-2 mb-8">
          {categories.map((cat) => {
            const IconComponent = categoryIcons[cat.id] || Sparkles;
            return (
              <button
                key={cat.id}
                onClick={() => handleCategoryChange(cat.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-full border transition-all ${
                  selectedCategory === cat.id 
                    ? "bg-primary text-primary-foreground border-primary" 
                    : "bg-card border-border hover:border-primary/50"
                }`}
                data-testid={`category-pill-${cat.id}`}
              >
                <IconComponent className="w-4 h-4" />
                <span className="text-sm font-medium">{cat.name}</span>
              </button>
            );
          })}
        </div>

        {/* Results */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        ) : professionals.length > 0 ? (
          <>
            <p className="text-muted-foreground mb-4">{professionals.length} professionals found</p>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {professionals.map((pro) => (
                <Link 
                  key={pro.user_id} 
                  to={`/professional/${pro.user_id}`}
                  data-testid={`professional-card-${pro.user_id}`}
                >
                  <Card className="h-full border-border hover:shadow-card-hover transition-all cursor-pointer overflow-hidden group">
                    <div className="relative h-32 bg-gradient-to-br from-primary/20 to-accent/20">
                      {pro.portfolio_images?.[0] && (
                        <img 
                          src={pro.portfolio_images[0]}
                          alt="Portfolio"
                          className="w-full h-full object-cover"
                        />
                      )}
                      <div className="absolute top-3 right-3">
                        {pro.match_score && (
                          <Badge className="bg-primary text-primary-foreground">
                            {pro.match_score}% Match
                          </Badge>
                        )}
                      </div>
                    </div>
                    <CardContent className="p-5">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h3 className="font-heading font-semibold text-lg group-hover:text-primary transition-colors">
                            {pro.user?.name || "Professional"}
                          </h3>
                          <p className="text-sm text-muted-foreground">{pro.profession}</p>
                        </div>
                        <div className="flex items-center gap-1 bg-primary/10 px-2 py-1 rounded-lg">
                          <Star className="w-4 h-4 text-primary fill-primary" />
                          <span className="font-medium text-sm">{pro.rating?.toFixed(1) || "New"}</span>
                        </div>
                      </div>
                      
                      <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
                        {pro.bio || "No bio available"}
                      </p>
                      
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-1 text-muted-foreground">
                          <MapPin className="w-4 h-4" />
                          <span>{pro.user?.location || "N/A"}</span>
                        </div>
                        <div className="flex items-center gap-1 text-primary font-semibold">
                          <DollarSign className="w-4 h-4" />
                          <span>KSh {pro.hourly_rate?.toLocaleString() || "N/A"}/hr</span>
                        </div>
                      </div>
                      
                      {pro.match_reason && (
                        <div className="mt-3 p-2 bg-accent/10 rounded-lg">
                          <p className="text-xs text-accent">{pro.match_reason}</p>
                        </div>
                      )}
                      
                      <div className="flex flex-wrap gap-2 mt-4">
                        {pro.skills?.slice(0, 3).map((skill, i) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          </>
        ) : (
          <div className="text-center py-20">
            <Search className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="font-heading text-xl font-semibold mb-2">No professionals found</h3>
            <p className="text-muted-foreground mb-6">Try adjusting your search or filters</p>
            <Button onClick={() => handleCategoryChange("all")} variant="outline" className="rounded-full">
              Clear Filters
            </Button>
          </div>
        )}
      </main>
    </div>
  );
}
