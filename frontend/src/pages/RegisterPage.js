import { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { useAuth } from "../context/AuthContext";
import { toast } from "sonner";
import { Eye, EyeOff, ArrowLeft, User, Briefcase, Phone, ShieldCheck, Loader2, CheckCircle2 } from "lucide-react";
import KaziLogo from "../components/KaziLogo";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const CLIENT_FEE = 20;
const PRO_FEE = 2000;

export default function RegisterPage() {
  const { setSession } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    password: "",
    role: "client",
    location: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  // Paywall dialog state
  const [paywallOpen, setPaywallOpen] = useState(false);
  const [paywallState, setPaywallState] = useState({
    status: "idle",           // 'idle' | 'awaiting_pin' | 'completed' | 'failed'
    amount: 0,
    fee_type: "",
    checkout_request_id: "",
    phone: "",
    reference: "",
    error: "",
    mpesa_receipt: "",
  });
  const pollTimerRef = useRef(null);
  const pollAttemptsRef = useRef(0);

  const fee = formData.role === "professional" ? PRO_FEE : CLIENT_FEE;
  const feeLabel = formData.role === "professional"
    ? "Professional Registration Fee"
    : "M-Pesa Account Verification Fee";

  useEffect(() => () => {
    if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleRoleSelect = (role) => {
    setFormData({ ...formData, role });
  };

  const startPolling = (checkout_request_id) => {
    pollAttemptsRef.current = 0;
    const poll = async () => {
      pollAttemptsRef.current += 1;
      try {
        const res = await axios.get(
          `${API}/auth/registration-status?checkout_request_id=${encodeURIComponent(checkout_request_id)}`
        );
        const data = res.data;
        if (data.status === "completed" && data.access_token && data.user) {
          setPaywallState((s) => ({ ...s, status: "completed", mpesa_receipt: data.mpesa_receipt }));
          // Hydrate auth context and redirect
          setSession({ token: data.access_token, user: data.user });
          toast.success("Welcome to Kazi Links!");
          setTimeout(() => {
            if (data.user.role === "client") navigate("/client");
            else if (data.user.role === "professional") navigate("/create-profile");
            else navigate("/");
          }, 1500);
          return;
        }
        if (data.status === "failed") {
          setPaywallState((s) => ({
            ...s,
            status: "failed",
            error: data.failure_reason || "M-Pesa payment failed. Please try again.",
          }));
          return;
        }
        // Keep polling up to ~3 minutes (90 attempts × 2s)
        if (pollAttemptsRef.current < 90) {
          pollTimerRef.current = setTimeout(poll, 2000);
        } else {
          setPaywallState((s) => ({
            ...s,
            status: "failed",
            error: "Payment not received in time. Please try again.",
          }));
        }
      } catch (err) {
        if (pollAttemptsRef.current < 90) {
          pollTimerRef.current = setTimeout(poll, 3000);
        }
      }
    };
    pollTimerRef.current = setTimeout(poll, 1500);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await axios.post(`${API}/auth/register-with-payment`, formData);
      setPaywallState({
        status: "awaiting_pin",
        amount: res.data.amount,
        fee_type: res.data.fee_type,
        checkout_request_id: res.data.checkout_request_id,
        phone: res.data.phone,
        reference: res.data.reference,
        error: "",
        mpesa_receipt: "",
      });
      setPaywallOpen(true);
      startPolling(res.data.checkout_request_id);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not start registration");
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    setPaywallOpen(false);
    setPaywallState({ status: "idle", amount: 0, fee_type: "", checkout_request_id: "", phone: "", reference: "", error: "", mpesa_receipt: "" });
    if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
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
                <KaziLogo size="md" />
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

                {/* Fee notice */}
                <div
                  className="rounded-xl border border-primary/30 bg-primary/5 p-3.5 text-sm"
                  data-testid="registration-fee-notice"
                >
                  <div className="flex items-start gap-2.5">
                    <ShieldCheck className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <p className="font-medium">{feeLabel}</p>
                        <p className="font-bold text-base text-primary">KSh {fee.toLocaleString()}</p>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {formData.role === "professional"
                          ? "One-time joining fee. After payment, you'll set up your pro profile."
                          : "Small fee charged via M-Pesa to verify your account and number."}{" "}
                        You'll receive an STK push on the phone above — enter your PIN to complete signup.
                      </p>
                    </div>
                  </div>
                </div>

                <Button 
                  type="submit" 
                  className="w-full h-12 rounded-xl bg-primary hover:bg-primary/90 font-medium"
                  disabled={loading}
                  data-testid="register-submit-btn"
                >
                  {loading
                    ? "Sending M-Pesa prompt..."
                    : `Pay KSh ${fee.toLocaleString()} & Create account`}
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

      {/* Paywall Dialog */}
      <Dialog open={paywallOpen} onOpenChange={(open) => { if (!open && paywallState.status !== "completed") handleRetry(); }}>
        <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto" data-testid="paywall-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-primary" />
              Complete payment
            </DialogTitle>
          </DialogHeader>

          {paywallState.status === "completed" ? (
            <div className="space-y-4 py-4 text-center" data-testid="paywall-completed">
              <div className="w-16 h-16 rounded-full bg-green-100 mx-auto flex items-center justify-center">
                <CheckCircle2 className="w-8 h-8 text-green-600" />
              </div>
              <div>
                <p className="font-heading font-bold text-lg">Payment received</p>
                <p className="text-sm text-muted-foreground">
                  M-Pesa receipt {paywallState.mpesa_receipt || ""}. Taking you to your dashboard…
                </p>
              </div>
              <Loader2 className="w-5 h-5 animate-spin text-muted-foreground mx-auto" />
            </div>
          ) : paywallState.status === "failed" ? (
            <div className="space-y-4 py-4 text-center" data-testid="paywall-failed">
              <div className="w-14 h-14 rounded-full bg-red-100 mx-auto flex items-center justify-center">
                <span className="text-2xl">!</span>
              </div>
              <div>
                <p className="font-heading font-bold text-lg">Payment failed</p>
                <p className="text-sm text-muted-foreground">{paywallState.error}</p>
              </div>
              <Button onClick={handleRetry} className="w-full rounded-xl" data-testid="paywall-retry">
                Try again
              </Button>
            </div>
          ) : (
            <div className="space-y-4" data-testid="paywall-awaiting">
              <div className="rounded-xl border border-border p-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Amount</span>
                  <span className="font-bold text-lg text-primary">KSh {Number(paywallState.amount).toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Phone</span>
                  <span className="font-mono">{paywallState.phone}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Reference</span>
                  <span className="font-mono text-xs">{paywallState.reference}</span>
                </div>
              </div>
              <div className="flex items-start gap-3 p-3 bg-amber-50 rounded-xl text-sm text-amber-900">
                <Phone className="w-4 h-4 mt-0.5 shrink-0" />
                <div className="flex-1">
                  <p className="font-medium">Check your phone</p>
                  <p className="text-xs">
                    We sent an M-Pesa prompt to{" "}
                    <span className="font-mono">{paywallState.phone}</span>. Enter your M-Pesa PIN to
                    complete payment. Your account is created automatically once payment is confirmed.
                  </p>
                </div>
              </div>
              <div className="flex items-center justify-center gap-2 text-muted-foreground text-sm" data-testid="paywall-waiting">
                <Loader2 className="w-4 h-4 animate-spin" />
                Waiting for payment confirmation…
              </div>
              <button
                onClick={handleRetry}
                className="text-xs text-muted-foreground hover:underline w-full text-center"
              >
                Cancel and edit details
              </button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
