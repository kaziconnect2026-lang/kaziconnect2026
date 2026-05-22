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
  Sparkles, Zap, Scissors, Droplet, PenTool, Wrench, Paintbrush, Hammer,
  SlidersHorizontal, ChevronRight,
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CACHE_VERSION = 2;
const CACHE_TTL_MS = 30 * 60 * 1000;
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
    localStorage.setItem(cacheKey(userId), JSON.stringify({ ...data, timestamp: Date.now() }));
  } catch { /* quota — ignore */ }
};

const categoryIcons = {
  barber: Scissors,
  electrician: Zap,
  plumber: Droplet,
  tattoo_artist: PenTool,
  car_mechanic: Wrench,
  mechanic: Wrench,
  painter: Paintbrush,
  carpenter: Hammer,
  cleaner: Sparkles,
  hairdresser: Scissors,
  nail_technician: PenTool,
};

const SORT_OPTIONS = [
  { value: "best_match", label: "Best match" },
  { value: "rating", label: "Top rated" },
  { value: "experience", label: "Most experienced" },
  { value: "reviews", label: "Most reviews" },
  { value: "price_low", label: "Price: low to high" },
  { value: "price_high", label: "Price: high to low" },
];

export default function SearchProfessionals() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const hasUrlFilter =
    !!searchParams.get("q") ||
    !!searchParams.get("location") ||
    !!searchParams.get("min_rating") ||
    !!searchParams.get("category");
  const cached = !hasUrlFilter ? readCache(user?.id) : null;

  const [searchQuery, setSearchQuery] = useState(searchParams.get("q") || cached?.filters?.searchQuery || "");
  const [locationQuery, setLocationQuery] = useState(searchParams.get("location") || cached?.filters?.locationQuery || "");
  const [minRating, setMinRating] = useState(searchParams.get("min_rating") || cached?.filters?.minRating || "");
  const [selectedCategory, setSelectedCategory] = useState(searchParams.get("category") || cached?.filters?.selectedCategory || "");
  const [sortBy, setSortBy] = useState(cached?.filters?.sortBy || "best_match");
  const [professionals, setProfessionals] = useState(cached?.results || []);
  const [categories, setCategories] = useState([]);
  const [categorySearch, setCategorySearch] = useState("");
  const [loading, setLoading] = useState(!cached);
  const [fromCache, setFromCache] = useState(!!cached);
  const [showMobileFilters, setShowMobileFilters] = useState(false);

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
      if (professionals.length === 0) setLoading(true);
      try {
        const params = new URLSearchParams();
        if (selectedCategory) params.append("category", selectedCategory);
        if (searchQuery.trim()) params.append("q", searchQuery.trim());
        if (locationQuery.trim()) params.append("location", locationQuery.trim());
        if (minRating) params.append("min_rating", minRating);
        if (sortBy) params.append("sort_by", sortBy);

        const response = await axios.get(`${API}/professionals/search?${params.toString()}`);
        setProfessionals(response.data);
        setFromCache(false);
        writeCache(user?.id, {
          filters: { searchQuery, locationQuery, minRating, selectedCategory, sortBy },
          results: response.data,
        });
      } catch (error) {
        console.error("Failed to fetch professionals:", error);
        toast.error("Failed to load professionals");
      } finally {
        setLoading(false);
      }
    };
    const t = setTimeout(fetchProfessionals, 300);
    return () => clearTimeout(t);
  }, [selectedCategory, searchQuery, locationQuery, minRating, sortBy, user?.id]);

  const handleCategoryChange = (value) => {
    setSelectedCategory(value === "all" ? "" : value);
    setSearchParams(value === "all" ? {} : { category: value });
    setCategorySearch("");
  };

  const clearAll = () => {
    setSearchQuery("");
    setLocationQuery("");
    setMinRating("");
    setSelectedCategory("");
    setSortBy("best_match");
    setSearchParams({});
    try { localStorage.removeItem(cacheKey(user?.id)); } catch { /* ignore */ }
    setFromCache(false);
  };

  const hasAnyFilter = !!(searchQuery || locationQuery || minRating || selectedCategory);
  const popularCategories = Object.values(categories).flat().slice(0, 12);

  return (
    <div className="min-h-screen bg-background" data-testid="search-page">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-border/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3 h-16">
            <button onClick={() => navigate(-1)} className="p-2 hover:bg-muted rounded-lg" data-testid="back-btn">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="font-heading font-semibold text-lg flex-1">Find a Professional</h1>
            <button
              onClick={() => setShowMobileFilters((v) => !v)}
              className="lg:hidden p-2 hover:bg-muted rounded-lg"
              data-testid="mobile-filters-toggle"
              aria-label="Toggle filters"
            >
              <SlidersHorizontal className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 grid lg:grid-cols-[280px_1fr] gap-6">
        {/* Sidebar — Filters */}
        <aside
          className={`${showMobileFilters ? "block" : "hidden"} lg:block space-y-5`}
          data-testid="filters-sidebar"
        >
          <Card className="border-border">
            <CardContent className="p-5 space-y-5">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-base flex items-center gap-2">
                  <Filter className="w-4 h-4 text-primary" />
                  Filters
                </h2>
                {hasAnyFilter && (
                  <button
                    onClick={clearAll}
                    className="text-xs font-medium text-primary hover:underline"
                    data-testid="clear-filters-btn"
                  >
                    Clear all
                  </button>
                )}
              </div>

              {/* Category */}
              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Category</label>
                <Select
                  value={selectedCategory || "all"}
                  onValueChange={handleCategoryChange}
                  onOpenChange={(open) => !open && setCategorySearch("")}
                >
                  <SelectTrigger className="rounded-xl h-11" data-testid="category-filter">
                    <SelectValue placeholder="All categories" />
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
                    {!categorySearch && <SelectItem value="all">All categories</SelectItem>}
                    {Object.entries(categories).map(([groupName, groupCats]) => {
                      const filteredCats = (groupCats || []).filter((cat) =>
                        cat.name.toLowerCase().includes(categorySearch.toLowerCase())
                      );
                      if (filteredCats.length === 0) return null;
                      return filteredCats.map((cat) => (
                        <SelectItem key={cat.id} value={cat.id}>{cat.name}</SelectItem>
                      ));
                    })}
                    {categorySearch && Object.values(categories).flat().filter((cat) =>
                      cat.name.toLowerCase().includes(categorySearch.toLowerCase())
                    ).length === 0 && (
                      <div className="px-2 py-4 text-center text-sm text-muted-foreground">
                        No matches for "{categorySearch}"
                      </div>
                    )}
                  </SelectContent>
                </Select>
              </div>

              {/* Location */}
              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Location</label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="e.g. Karen, Westlands"
                    value={locationQuery}
                    onChange={(e) => setLocationQuery(e.target.value)}
                    className="pl-9 h-11 rounded-xl"
                    data-testid="location-filter"
                  />
                </div>
              </div>

              {/* Rating */}
              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Minimum rating</label>
                <Select
                  value={minRating || "any"}
                  onValueChange={(v) => setMinRating(v === "any" ? "" : v)}
                >
                  <SelectTrigger className="rounded-xl h-11" data-testid="rating-filter">
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
              </div>

              {/* Name / keyword search */}
              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Search by name or skill</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="e.g. john, plumbing"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9 h-11 rounded-xl"
                    data-testid="search-input"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Popular categories quick-pick */}
          {popularCategories.length > 0 && (
            <Card className="border-border">
              <CardContent className="p-5 space-y-3">
                <h3 className="font-semibold text-sm">Popular categories</h3>
                <div className="flex flex-wrap gap-2">
                  {popularCategories.map((cat) => {
                    const IconComponent = categoryIcons[cat.id] || Sparkles;
                    const active = selectedCategory === cat.id;
                    return (
                      <button
                        key={cat.id}
                        onClick={() => handleCategoryChange(cat.id)}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-all ${
                          active
                            ? "bg-primary text-primary-foreground border-primary"
                            : "bg-card border-border hover:border-primary/40"
                        }`}
                        data-testid={`category-pill-${cat.id}`}
                      >
                        <IconComponent className="w-3.5 h-3.5" />
                        {cat.name}
                      </button>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}
        </aside>

        {/* Results */}
        <section>
          {/* Result toolbar */}
          <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
            <div className="flex items-center gap-3 flex-wrap">
              {!loading && (
                <p className="text-sm text-muted-foreground" data-testid="results-count">
                  <span className="font-semibold text-foreground">{professionals.length}</span>{" "}
                  professional{professionals.length === 1 ? "" : "s"} found
                </p>
              )}
              {fromCache && (
                <span
                  className="text-[11px] text-muted-foreground inline-flex items-center gap-1 bg-muted px-2 py-0.5 rounded-full"
                  data-testid="cached-results-badge"
                >
                  <Clock className="w-3 h-3" />
                  Showing your last search
                </span>
              )}
            </div>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-52 rounded-xl h-10" data-testid="sort-filter">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SORT_OPTIONS.map((s) => (
                  <SelectItem key={s.value} value={s.value}>Sort: {s.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Active filter chips */}
          {hasAnyFilter && (
            <div className="flex flex-wrap gap-2 mb-5" data-testid="active-filter-chips">
              {selectedCategory && (
                <Chip
                  label={
                    Object.values(categories).flat().find((c) => c.id === selectedCategory)?.name ||
                    selectedCategory
                  }
                  onRemove={() => handleCategoryChange("all")}
                  testId="chip-category"
                />
              )}
              {locationQuery && (
                <Chip
                  label={`${locationQuery}`}
                  icon={<MapPin className="w-3 h-3" />}
                  onRemove={() => setLocationQuery("")}
                  testId="chip-location"
                />
              )}
              {minRating && (
                <Chip
                  label={`${minRating}+ stars`}
                  icon={<Star className="w-3 h-3" />}
                  onRemove={() => setMinRating("")}
                  testId="chip-rating"
                />
              )}
              {searchQuery && (
                <Chip
                  label={`"${searchQuery}"`}
                  icon={<Search className="w-3 h-3" />}
                  onRemove={() => setSearchQuery("")}
                  testId="chip-query"
                />
              )}
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
          ) : professionals.length > 0 ? (
            <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
              {professionals.map((pro) => (
                <Link
                  key={pro.user_id}
                  to={`/professional/${pro.user_id}`}
                  data-testid={`professional-card-${pro.user_id}`}
                >
                  <Card className="h-full border-border hover:shadow-card-hover transition-all cursor-pointer overflow-hidden group">
                    <div className="relative h-28 bg-gradient-to-br from-primary/20 to-accent/20">
                      {pro.portfolio_images?.[0] && (
                        <img
                          src={pro.portfolio_images[0]}
                          alt="Portfolio"
                          className="w-full h-full object-cover"
                        />
                      )}
                      {pro.availability && (
                        <Badge className="absolute top-3 left-3 bg-green-100 text-green-800 border-0">
                          Available
                        </Badge>
                      )}
                    </div>
                    <CardContent className="p-5">
                      <div className="flex items-start justify-between mb-2 gap-2">
                        <div className="min-w-0">
                          <h3 className="font-heading font-semibold text-base group-hover:text-primary transition-colors truncate">
                            {pro.user?.name || "Professional"}
                          </h3>
                          <p className="text-sm text-muted-foreground truncate">{pro.profession}</p>
                        </div>
                        <div className="flex items-center gap-1 bg-primary/10 px-2 py-1 rounded-lg shrink-0">
                          <Star className="w-3.5 h-3.5 text-primary fill-primary" />
                          <span className="font-medium text-sm">{pro.rating?.toFixed(1) || "New"}</span>
                          {pro.total_reviews > 0 && (
                            <span className="text-[11px] text-muted-foreground">({pro.total_reviews})</span>
                          )}
                        </div>
                      </div>

                      <p className="text-sm text-muted-foreground line-clamp-2 mb-4 min-h-[2.5rem]">
                        {pro.bio || "No bio provided."}
                      </p>

                      <div className="flex items-center justify-between text-sm mb-3">
                        <div className="flex items-center gap-1 text-muted-foreground min-w-0">
                          <MapPin className="w-4 h-4 shrink-0" />
                          <span className="truncate">{pro.user?.location || "Location N/A"}</span>
                        </div>
                        <div className="flex items-center gap-1 text-primary font-semibold shrink-0">
                          <DollarSign className="w-4 h-4" />
                          <span>KSh {pro.hourly_rate?.toLocaleString() || "—"}/hr</span>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-1.5">
                        {(pro.skills || []).slice(0, 3).map((skill, i) => (
                          <Badge key={i} variant="outline" className="text-[11px] font-normal">{skill}</Badge>
                        ))}
                        {pro.experience_years > 0 && (
                          <Badge variant="outline" className="text-[11px] font-normal">
                            {pro.experience_years}y exp
                          </Badge>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState onClear={clearAll} hasFilters={hasAnyFilter} />
          )}
        </section>
      </main>
    </div>
  );
}

function Chip({ label, icon, onRemove, testId }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 bg-primary/10 text-primary px-3 py-1 rounded-full text-xs font-medium"
      data-testid={testId}
    >
      {icon}
      {label}
      <button
        onClick={onRemove}
        className="ml-1 hover:bg-primary/20 rounded-full w-4 h-4 inline-flex items-center justify-center"
        aria-label={`Remove ${label}`}
      >
        ×
      </button>
    </span>
  );
}

function EmptyState({ onClear, hasFilters }) {
  return (
    <div className="text-center py-16" data-testid="empty-state">
      <div className="w-16 h-16 rounded-2xl bg-muted mx-auto mb-4 flex items-center justify-center">
        <Search className="w-8 h-8 text-muted-foreground" />
      </div>
      <h3 className="font-heading text-lg font-semibold mb-2">No professionals found</h3>
      <p className="text-sm text-muted-foreground mb-6 max-w-md mx-auto">
        {hasFilters
          ? "Try removing one of your filters, or pick a different category."
          : "No professionals are available right now. Check back soon."}
      </p>
      {hasFilters && (
        <Button onClick={onClear} variant="outline" className="rounded-full" data-testid="empty-clear-btn">
          Clear filters
          <ChevronRight className="w-4 h-4 ml-1" />
        </Button>
      )}
    </div>
  );
}
