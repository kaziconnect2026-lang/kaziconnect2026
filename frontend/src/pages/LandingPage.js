import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent } from "../components/ui/card";
import { useAuth } from "../context/AuthContext";
import { Search, Star, Shield, Clock, MapPin, ChevronRight, Zap, Scissors, Droplet, PenTool, Wrench, Paintbrush, Hammer, Sparkles } from "lucide-react";
import axios from "axios";

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

export default function LandingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await axios.get(`${API}/categories/featured`);
        setCategories(response.data);
      } catch (error) {
        console.error("Failed to fetch categories:", error);
      }
    };
    fetchCategories();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (user) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
    } else {
      navigate("/login");
    }
  };

  const handleCategoryClick = (categoryId) => {
    if (user) {
      navigate(`/search?category=${categoryId}`);
    } else {
      navigate("/login");
    }
  };

  return (
    <div className="min-h-screen bg-background" data-testid="landing-page">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
                <span className="text-primary-foreground font-heading font-bold text-xl">K</span>
              </div>
              <span className="font-heading font-bold text-xl text-foreground">Kazi Links</span>
            </div>
            
            <div className="flex items-center gap-4">
              {user ? (
                <Button 
                  onClick={() => navigate(user.role === "client" ? "/client" : user.role === "professional" ? "/professional" : "/admin")}
                  className="rounded-full px-6"
                  data-testid="dashboard-btn"
                >
                  Dashboard
                </Button>
              ) : (
                <>
                  <Link to="/login">
                    <Button variant="ghost" className="font-medium" data-testid="login-btn">
                      Log in
                    </Button>
                  </Link>
                  <Link to="/register">
                    <Button className="rounded-full px-6 bg-primary hover:bg-primary/90" data-testid="signup-btn">
                      Sign up
                    </Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4" data-testid="hero-section">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-4xl mx-auto">
            <h1 className="font-heading text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground leading-tight mb-6">
              Find the Best <span className="text-primary">Skilled Pros</span> in Your Area
            </h1>
            <p className="text-lg text-muted-foreground mb-10 max-w-2xl mx-auto">
              Connect with trusted barbers, electricians, plumbers, tattoo artists, and more. Quality service, just a tap away.
            </p>
            
            {/* Search Bar */}
            <form onSubmit={handleSearch} className="max-w-2xl mx-auto">
              <div className="flex gap-3 p-2 bg-card rounded-2xl shadow-card border border-border">
                <div className="flex-1 flex items-center gap-3 px-4">
                  <Search className="w-5 h-5 text-muted-foreground" />
                  <Input 
                    type="text"
                    placeholder="What service do you need?"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="border-0 bg-transparent focus-visible:ring-0 text-base placeholder:text-muted-foreground"
                    data-testid="search-input"
                  />
                </div>
                <Button 
                  type="submit" 
                  size="lg"
                  className="rounded-xl px-8 bg-primary hover:bg-primary/90"
                  data-testid="search-btn"
                >
                  Search
                </Button>
              </div>
            </form>
          </div>

          {/* Hero Images Grid */}
          <div className="mt-16 grid grid-cols-3 gap-4 max-w-4xl mx-auto">
            <div className="col-span-2 row-span-2 relative rounded-3xl overflow-hidden aspect-[4/3]">
              <img 
                src="https://images.unsplash.com/photo-1599641078447-229873aedbc8?crop=entropy&cs=srgb&fm=jpg&q=85&w=800"
                alt="Professional barber at work"
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
              <div className="absolute bottom-6 left-6 text-white">
                <p className="text-sm font-medium opacity-80">Featured Pro</p>
                <p className="text-xl font-heading font-bold">Barbers & Stylists</p>
              </div>
            </div>
            <div className="relative rounded-2xl overflow-hidden aspect-square">
              <img 
                src="https://images.unsplash.com/photo-1621905252507-b35492cc74b4?crop=entropy&cs=srgb&fm=jpg&q=85&w=400"
                alt="Electrician"
                className="w-full h-full object-cover"
              />
            </div>
            <div className="relative rounded-2xl overflow-hidden aspect-square">
              <img 
                src="https://images.pexels.com/photos/8486978/pexels-photo-8486978.jpeg?w=400"
                alt="Plumber"
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Categories Section */}
      <section className="py-20 px-4 bg-muted/30" data-testid="categories-section">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="font-heading text-3xl sm:text-4xl font-bold text-foreground mb-4">
              Browse by Category
            </h2>
            <p className="text-muted-foreground">Find professionals in any field you need</p>
          </div>
          
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
            {categories.map((category, index) => {
              const IconComponent = categoryIcons[category.id] || Sparkles;
              return (
                <Card 
                  key={category.id}
                  className="group cursor-pointer border-border bg-card hover:shadow-card-hover transition-all duration-300 overflow-hidden"
                  onClick={() => handleCategoryClick(category.id)}
                  style={{ animationDelay: `${index * 50}ms` }}
                  data-testid={`category-${category.id}`}
                >
                  <div className="relative h-32 sm:h-40 overflow-hidden">
                    <img 
                      src={category.image}
                      alt={category.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
                    <div className="absolute bottom-4 left-4 flex items-center gap-2">
                      <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                        <IconComponent className="w-4 h-4 text-primary-foreground" />
                      </div>
                      <span className="font-heading font-semibold text-white">{category.name}</span>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-4" data-testid="how-it-works">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-heading text-3xl sm:text-4xl font-bold text-foreground mb-4">
              How It Works
            </h2>
            <p className="text-muted-foreground">Get connected with professionals in 3 easy steps</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Search,
                title: "Search & Browse",
                description: "Find professionals by category, location, ratings, and price range.",
                step: "01"
              },
              {
                icon: Star,
                title: "Compare & Choose",
                description: "View profiles, portfolios, reviews, and pricing to make the best choice.",
                step: "02"
              },
              {
                icon: Shield,
                title: "Book Securely",
                description: "Pay via M-Pesa escrow. Funds are released only when the job is done.",
                step: "03"
              }
            ].map((item, index) => (
              <Card key={index} className="relative border-border bg-card p-8 text-center group hover:shadow-card-hover transition-all">
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                  <span className="text-primary-foreground font-bold text-sm">{item.step}</span>
                </div>
                <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:bg-primary/20 transition-colors">
                  <item.icon className="w-8 h-8 text-primary" />
                </div>
                <h3 className="font-heading font-bold text-xl mb-3">{item.title}</h3>
                <p className="text-muted-foreground">{item.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Trust & Safety */}
      <section className="py-20 px-4 bg-secondary text-secondary-foreground" data-testid="trust-section">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="font-heading text-3xl sm:text-4xl font-bold mb-6">
                Trust & Safety First
              </h2>
              <p className="text-secondary-foreground/80 mb-8">
                We prioritize your security with our M-Pesa escrow payment system. Your money is held safely until you confirm the job is complete.
              </p>
              <div className="space-y-4">
                {[
                  { icon: Shield, text: "Secure M-Pesa escrow payments" },
                  { icon: Star, text: "Verified reviews from real clients" },
                  { icon: Clock, text: "24/7 customer support" },
                  { icon: MapPin, text: "Location-based matching" }
                ].map((item, index) => (
                  <div key={index} className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-primary/20 rounded-xl flex items-center justify-center">
                      <item.icon className="w-5 h-5 text-primary" />
                    </div>
                    <span className="text-secondary-foreground/90">{item.text}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="relative">
              <div className="bg-card rounded-3xl p-8 text-foreground">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 bg-accent rounded-2xl flex items-center justify-center">
                    <Shield className="w-8 h-8 text-accent-foreground" />
                  </div>
                  <div>
                    <p className="text-3xl font-heading font-bold">20%</p>
                    <p className="text-muted-foreground">Platform Fee</p>
                  </div>
                </div>
                <p className="text-muted-foreground mb-4">
                  We charge a transparent 20% fee for connecting you with trusted professionals and providing secure payment protection.
                </p>
                <div className="flex items-center gap-2 text-accent">
                  <span className="font-medium">Learn more</span>
                  <ChevronRight className="w-4 h-4" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA for Professionals */}
      <section className="py-20 px-4" data-testid="pro-cta">
        <div className="max-w-4xl mx-auto text-center">
          <div className="bg-gradient-to-br from-primary/10 to-accent/10 rounded-3xl p-12 border border-primary/20">
            <h2 className="font-heading text-3xl sm:text-4xl font-bold text-foreground mb-4">
              Are You a Skilled Professional?
            </h2>
            <p className="text-muted-foreground mb-8 max-w-2xl mx-auto">
              Join Kazi Links and connect with clients looking for your expertise. Set your own rates, manage your schedule, and grow your business.
            </p>
            <Link to="/register">
              <Button size="lg" className="rounded-full px-8 bg-primary hover:bg-primary/90" data-testid="join-as-pro-btn">
                Join as a Professional
                <ChevronRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-border bg-muted/30">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
                <span className="text-primary-foreground font-heading font-bold text-xl">K</span>
              </div>
              <span className="font-heading font-bold text-xl text-foreground">Kazi Links</span>
            </div>
            <p className="text-muted-foreground text-sm">
              © 2024 Kazi Links. Empowering work, building trust.
            </p>
            <div className="flex gap-6">
              <a href="#" className="text-muted-foreground hover:text-foreground transition-colors">Terms</a>
              <a href="#" className="text-muted-foreground hover:text-foreground transition-colors">Privacy</a>
              <a href="#" className="text-muted-foreground hover:text-foreground transition-colors">Contact</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
