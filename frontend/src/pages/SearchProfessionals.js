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

const CACHE_VERSION = 1;
const CACHE_TTL_MS = 30 * 60 * 1000; // 30 minutes
const cacheKey = (userId) => `kazi_search_cache_${userId || "anon"}_v${CACHE_VERSION}`;

const readCache = (userId) => {
  try {
    const raw = localStorage.getItem(cacheKey(userId));
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || (Date.now() - (parsed.timestamp || 0) > CACHE_TTL_MS)) return null;
    return parsed;
  } catch {
    return null;
  }
};

const writeCache = (userId, data) => {
  try {
    localStorage.setItem(
      cacheKey(userId),
      JSON.stringify({ ...data, timestamp: Date.now() })
    );
  } catch {
    /* quota or serialization error — ignore */
  }
};

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

  // Hydrate from URL params first; fall back to cached state (URL has any param → ignore cache)
  const hasUrlFilter =
    !!searchParams.get("q") ||
    !!searchParams.get("location") ||
    !!searchParams.get("min_rating") ||
    !!searchParams.get("category");
  const cached = !hasUrlFilter ? readCache(user?.id) : null;

  const [searchQuery, setSearchQuery] = useState(
    searchParams.get("q") || cached?.filters?.searchQuery || ""
  );
  const [locationQuery, setLocationQuery] = useState(
    searchParams.get("location") || cached?.filters?.locationQuery || ""
  );
  const [minRating, setMinRating] = useState(
    searchParams.get("min_rating") || cached?.filters?.minRating || ""
  );
  const [selectedCategory, setSelectedCategory] = useState(
    searchParams.get("category") || cached?.filters?.selectedCategory || ""
  );
  const [professionals, setProfessionals] = useState(cached?.results || []);
  const [categories, setCategories] = useState([]);
  const [categorySearch, setCategorySearch] = useState("");
  // Show loading only if there is no cached snapshot to display
  const [loading, setLoading] = useState(!cached);
  const [aiMatching, setAiMatching] = useState(false);
  const [fromCache, setFromCache] = useState(!!cached);

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
      // Show spinner only when there's nothing to display; refresh silently otherwise
      const hasResultsAlready = professionals.length > 0;
      if (!hasResultsAlready) setLoading(true);
      try {
        const params = new URLSearchParams();
        if (selectedCategory) params.append("category", selectedCategory);
        if (searchQuery.trim()) params.append("q", searchQuery.trim());
        if (locationQuery.trim()) params.append("location", locationQuery.trim());
        if (minRating) params.append("min_rating", minRating);

        const response = await axios.get(`${API}/professionals/search?${params.toString()}`);
        setProfessionals(response.data);
        setFromCache(false);
        writeCache(user?.id, {
          filters: { searchQuery, locationQuery, minRating, selectedCategory },
          results: response.data,
          mode: "search",
        });
      } catch (error) {
        console.error("Failed to fetch professionals:", error);
        toast.error("Failed to load professionals");
      } finally {
        setLoading(false);
      }
    };
    // Debounce text inputs by 300ms; categories & rating fire immediately
    const t = setTimeout(fetchProfessionals, 300);
    return () => clearTimeout(t);
  }, [selectedCategory, searchQuery, locationQuery, minRating, user?.id]);

  const handleAIMatch = async () => {
    if (!searchQuery.trim()) {
      toast.error("Type what you need (e.g., 'plumber to fix sink in Westlands')");
      return;
    }

    setAiMatching(true);
    try {
      const response = await axios.post(`${API}/match`, {
        query: searchQuery.trim(),
        category: selectedCategory || null,
        location: locationQuery.trim() || user?.location || null,
      });

      const matches = response.data.matches || [];
      setProfessionals(matches);
      setFromCache(false);
      writeCache(user?.id, {
        filters: { searchQuery, locationQuery, minRating, selectedCategory },
        results: matches,
        mode: "ai",
        ai_powered: !!response.data.ai_powered,
      });

      if (matches.length === 0) {
        toast.info(response.data.message || "No professionals matched. Try a different keyword.");
      } else if (response.data.ai_powered) {
        toast.success(`AI found ${matches.length} match${matches.length === 1 ? "" : "es"}`);
      } else {
        toast.success(`${matches.length} professional${matches.length === 1 ? "" : "s"} found`);
      }
    } catch (error) {
      console.error("AI matching failed:", error);
      toast.error(error.response?.data?.detail || "AI matching failed. Try again.");
    } finally {
      setAiMatching(false);
    }
  };

  const handleCategoryChange = (value) => {
    setSelectedCategory(value === "all" ? "" : value);
    setSearchParams(value === "all" ? {} : { category: value });
    setCategorySearch("");
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
                  placeholder="Search by name, profession or skill..."
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
          <Select 
            value={selectedCategory || "all"} 
            onValueChange={handleCategoryChange}
            onOpenChange={(open) => !open && setCategorySearch("")}
          >
            <SelectTrigger className="w-48 rounded-xl" data-testid="category-filter">
              <SelectValue placeholder="All Categories" />
            </SelectTrigger>
            <SelectContent className="max-h-80">
              <div className="px-2 py-2 sticky top-0 bg-background z-10 border-b">
                <div className="relative">
                  <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Search categories..."
                    value={categorySearch}
                    onChange={(e) => setCategorySearch(e.target.value)}
                    className="pl-8 h-9"
                    data-testid="category-search-filter"
                  />
                </div>
              </div>
              {!categorySearch && <SelectItem value="all">All Categories</SelectItem>}
              {Object.entries(categories).map(([groupName, groupCats]) => {
                const filteredCats = groupCats.filter(cat => 
                  cat.name.toLowerCase().includes(categorySearch.toLowerCase())
                );
                if (filteredCats.length === 0) return null;
                return filteredCats.map((cat) => (
                  <SelectItem key={cat.id} value={cat.id}>{cat.name}</SelectItem>
                ));
              })}
              {categorySearch && Object.values(categories).flat().filter(cat => 
                cat.name.toLowerCase().includes(categorySearch.toLowerCase())
              ).length === 0 && (
                <div className="px-2 py-4 text-center text-sm text-muted-foreground">
                  No categories found for "{categorySearch}"
                </div>
              )}
            </SelectContent>
          </Select>

          {/* Location filter */}
          <div className="relative">
            <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Location"
              value={locationQuery}
              onChange={(e) => setLocationQuery(e.target.value)}
              className="pl-9 w-44 h-10 rounded-xl"
              data-testid="location-filter"
            />
          </div>

          {/* Rating filter */}
          <Select
            value={minRating || "any"}
            onValueChange={(v) => setMinRating(v === "any" ? "" : v)}
          >
            <SelectTrigger className="w-40 rounded-xl" data-testid="rating-filter">
              <SelectValue placeholder="Any rating" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="any">Any rating</SelectItem>
              <SelectItem value="4.5">4.5+ stars</SelectItem>
              <SelectItem value="4">4+ stars</SelectItem>
              <SelectItem value="3">3+ stars</SelectItem>
              <SelectItem value="2">2+ stars</SelectItem>
            </SelectContent>
          </Select>

          {(searchQuery || locationQuery || minRating || selectedCategory) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSearchQuery("");
                setLocationQuery("");
                setMinRating("");
                setSelectedCategory("");
                setSearchParams({});
                try { localStorage.removeItem(cacheKey(user?.id)); } catch {/* ignore */}
                setFromCache(false);
              }}
              className="text-muted-foreground hover:text-foreground"
              data-testid="clear-filters-btn"
            >
              Clear
            </Button>
          )}
        </div>

        {/* Category Pills - Show first 8 popular categories */}
        <div className="flex flex-wrap gap-2 mb-8">
          {Object.values(categories).flat().slice(0, 12).map((cat) => {
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
            <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
              <p className="text-muted-foreground" data-testid="results-count">
                {professionals.length} professional{professionals.length === 1 ? "" : "s"} found
              </p>
              {fromCache && (
                <span
                  className="text-xs text-muted-foreground inline-flex items-center gap-1.5 bg-muted px-2.5 py-1 rounded-full"
                  data-testid="cached-results-badge"
                >
                  <Clock className="w-3 h-3" />
                  Showing your last search · refreshing...
                </span>
              )}
            </div>
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
