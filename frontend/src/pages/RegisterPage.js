import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { useAuth } from "../context/AuthContext";
import { toast } from "sonner";
import { Eye, EyeOff, ArrowLeft, User, Briefcase } from "lucide-react";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    password: "",
    role: "client",
    location: ""
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleRoleSelect = (role) => {
    setFormData({ ...formData, role });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const result = await register(formData);
    
    if (result.success) {
      toast.success("Account created successfully!");
      // Navigate based on role
      if (result.user.role === "client") {
        navigate("/client");
      } else if (result.user.role === "professional") {
        navigate("/create-profile");
      }
    } else {
      toast.error(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-background flex" data-testid="register-page">
      {/* Left side - Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <Link to="/" className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground mb-8 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to home
          </Link>
          
          <Card className="border-border shadow-card">
            <CardHeader className="space-y-1 pb-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
                  <span className="text-primary-foreground font-heading font-bold text-xl">K</span>
                </div>
                <span className="font-heading font-bold text-xl">Kazi Links</span>
              </div>
              <CardTitle className="font-heading text-2xl">Create an account</CardTitle>
              <CardDescription>Join the Kazi Links community today</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Role Selection */}
                <div className="space-y-2">
                  <Label>I want to</Label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => handleRoleSelect("client")}
                      className={`p-4 rounded-xl border-2 transition-all flex flex-col items-center gap-2 ${
                        formData.role === "client" 
                          ? "border-primary bg-primary/5" 
                          : "border-border hover:border-primary/50"
                      }`}
                      data-testid="role-client-btn"
                    >
                      <User className={`w-6 h-6 ${formData.role === "client" ? "text-primary" : "text-muted-foreground"}`} />
                      <span className={`font-medium ${formData.role === "client" ? "text-primary" : "text-muted-foreground"}`}>
                        Find Pros
                      </span>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleRoleSelect("professional")}
                      className={`p-4 rounded-xl border-2 transition-all flex flex-col items-center gap-2 ${
                        formData.role === "professional" 
                          ? "border-primary bg-primary/5" 
                          : "border-border hover:border-primary/50"
                      }`}
                      data-testid="role-professional-btn"
                    >
                      <Briefcase className={`w-6 h-6 ${formData.role === "professional" ? "text-primary" : "text-muted-foreground"}`} />
                      <span className={`font-medium ${formData.role === "professional" ? "text-primary" : "text-muted-foreground"}`}>
                        Offer Services
                      </span>
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    name="name"
                    type="text"
                    placeholder="John Doe"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    className="h-12"
                    data-testid="name-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="name@example.com"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="h-12"
                    data-testid="email-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input
                    id="phone"
                    name="phone"
                    type="tel"
                    placeholder="+254 712 345 678"
                    value={formData.phone}
                    onChange={handleChange}
                    required
                    className="h-12"
                    data-testid="phone-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="location">Location</Label>
                  <Input
                    id="location"
                    name="location"
                    type="text"
                    placeholder="Nairobi, Kenya"
                    value={formData.location}
                    onChange={handleChange}
                    className="h-12"
                    data-testid="location-input"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      name="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="Create a password"
                      value={formData.password}
                      onChange={handleChange}
                      required
                      minLength={6}
                      className="h-12 pr-12"
                      data-testid="password-input"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                <Button 
                  type="submit" 
                  className="w-full h-12 rounded-xl bg-primary hover:bg-primary/90 font-medium"
                  disabled={loading}
                  data-testid="register-submit-btn"
                >
                  {loading ? "Creating account..." : "Create account"}
                </Button>
              </form>

              <div className="mt-6 text-center text-sm">
                <span className="text-muted-foreground">Already have an account? </span>
                <Link to="/login" className="text-primary hover:underline font-medium" data-testid="login-link">
                  Sign in
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Right side - Image */}
      <div className="hidden lg:flex flex-1 bg-secondary items-center justify-center p-12">
        <div className="max-w-lg">
          <div className="relative rounded-3xl overflow-hidden mb-8">
            <img 
              src="https://images.unsplash.com/photo-1599641078447-229873aedbc8?crop=entropy&cs=srgb&fm=jpg&q=85&w=600"
              alt="Professional barber"
              className="w-full aspect-[4/3] object-cover"
            />
          </div>
          <div className="text-secondary-foreground">
            <h3 className="font-heading text-2xl font-bold mb-4">Join thousands of professionals</h3>
            <ul className="space-y-3">
              <li className="flex items-center gap-3">
                <div className="w-6 h-6 bg-accent rounded-full flex items-center justify-center">
                  <span className="text-accent-foreground text-sm">✓</span>
                </div>
                <span>Set your own rates and schedule</span>
              </li>
              <li className="flex items-center gap-3">
                <div className="w-6 h-6 bg-accent rounded-full flex items-center justify-center">
                  <span className="text-accent-foreground text-sm">✓</span>
                </div>
                <span>Get paid securely via M-Pesa</span>
              </li>
              <li className="flex items-center gap-3">
                <div className="w-6 h-6 bg-accent rounded-full flex items-center justify-center">
                  <span className="text-accent-foreground text-sm">✓</span>
                </div>
                <span>Build your reputation with reviews</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
