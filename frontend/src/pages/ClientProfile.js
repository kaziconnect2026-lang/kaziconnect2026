import { useState, useEffect, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { 
  ArrowLeft, Camera, User, Mail, Phone, MapPin, 
  Calendar, Wallet, Briefcase, Save, Edit2
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ClientProfile() {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [stats, setStats] = useState({ total_bookings: 0, total_spent: 0, total_jobs: 0 });
  const [formData, setFormData] = useState({
    name: "",
    phone: "",
    location: "",
    profile_photo: null
  });
  const [photoPreview, setPhotoPreview] = useState(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);

  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name || "",
        phone: user.phone || "",
        location: user.location || "",
        profile_photo: user.profile_photo || null
      });
      setPhotoPreview(user.profile_photo);
    }
    fetchStats();
  }, [user]);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/client`);
      setStats({
        total_bookings: response.data.active_bookings?.length || 0,
        total_spent: response.data.total_spent || 0,
        total_jobs: response.data.recent_jobs?.length || 0
      });
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  const handlePhotoSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      toast.error("Image must be less than 5MB");
      return;
    }

    const reader = new FileReader();
    reader.onloadend = () => {
      setPhotoPreview(reader.result);
      handlePhotoUpload(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handlePhotoUpload = async (base64Data) => {
    setUploadingPhoto(true);
    try {
      await axios.post(`${API}/users/profile-photo?photo_url=${encodeURIComponent(base64Data)}`);
      setFormData({ ...formData, profile_photo: base64Data });
      toast.success("Profile photo updated!");
      if (refreshUser) refreshUser();
    } catch (error) {
      toast.error("Failed to upload photo");
      setPhotoPreview(formData.profile_photo);
    } finally {
      setUploadingPhoto(false);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.put(`${API}/users/profile`, {
        name: formData.name,
        phone: formData.phone,
        location: formData.location
      });
      toast.success("Profile updated successfully!");
      setIsEditing(false);
      if (refreshUser) refreshUser();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to update profile");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background" data-testid="client-profile-page">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-border/40">
        <div className="max-w-2xl mx-auto px-4 h-16 flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-muted rounded-lg" data-testid="back-btn">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="font-heading font-semibold">My Profile</h1>
          {!isEditing && (
            <button 
              onClick={() => setIsEditing(true)} 
              className="ml-auto p-2 hover:bg-muted rounded-lg"
              data-testid="edit-profile-btn"
            >
              <Edit2 className="w-5 h-5" />
            </button>
          )}
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-6 pb-24">
        {/* Profile Photo Section */}
        <Card className="border-border mb-6 overflow-hidden">
          <div className="h-24 bg-gradient-to-br from-primary/30 to-accent/30" />
          <CardContent className="relative pt-0">
            <div className="flex flex-col items-center -mt-12">
              <div className="relative">
                <div className="w-24 h-24 bg-card border-4 border-background rounded-full flex items-center justify-center overflow-hidden">
                  {photoPreview ? (
                    <img 
                      src={photoPreview} 
                      alt="Profile" 
                      className="w-full h-full object-cover"
                      data-testid="profile-photo"
                    />
                  ) : (
                    <User className="w-10 h-10 text-muted-foreground" />
                  )}
                </div>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="absolute bottom-0 right-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground shadow-lg hover:bg-primary/90 transition-colors"
                  disabled={uploadingPhoto}
                  data-testid="change-photo-btn"
                >
                  {uploadingPhoto ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <Camera className="w-4 h-4" />
                  )}
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handlePhotoSelect}
                  data-testid="photo-input"
                />
              </div>
              <h2 className="font-heading text-xl font-bold mt-4">{user?.name}</h2>
              <p className="text-sm text-muted-foreground">{user?.display_id || "Client"}</p>
            </div>
          </CardContent>
        </Card>

        {/* Stats Section */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <Card className="border-border">
            <CardContent className="p-4 text-center">
              <Briefcase className="w-5 h-5 text-primary mx-auto mb-2" />
              <p className="text-lg font-bold">{stats.total_jobs}</p>
              <p className="text-xs text-muted-foreground">Jobs Posted</p>
            </CardContent>
          </Card>
          <Card className="border-border">
            <CardContent className="p-4 text-center">
              <Calendar className="w-5 h-5 text-primary mx-auto mb-2" />
              <p className="text-lg font-bold">{stats.total_bookings}</p>
              <p className="text-xs text-muted-foreground">Bookings</p>
            </CardContent>
          </Card>
          <Card className="border-border">
            <CardContent className="p-4 text-center">
              <Wallet className="w-5 h-5 text-primary mx-auto mb-2" />
              <p className="text-lg font-bold">KSh {stats.total_spent.toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">Total Spent</p>
            </CardContent>
          </Card>
        </div>

        {/* Profile Form */}
        <Card className="border-border">
          <CardHeader>
            <CardTitle className="font-heading">Profile Information</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="name" className="flex items-center gap-2">
                  <User className="w-4 h-4 text-muted-foreground" />
                  Full Name
                </Label>
                <Input
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="h-12"
                  data-testid="name-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="email" className="flex items-center gap-2">
                  <Mail className="w-4 h-4 text-muted-foreground" />
                  Email Address
                </Label>
                <Input
                  id="email"
                  value={user?.email || ""}
                  disabled
                  className="h-12 bg-muted/50"
                  data-testid="email-input"
                />
                <p className="text-xs text-muted-foreground">Email cannot be changed</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="phone" className="flex items-center gap-2">
                  <Phone className="w-4 h-4 text-muted-foreground" />
                  Phone Number
                </Label>
                <Input
                  id="phone"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="h-12"
                  data-testid="phone-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="location" className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-muted-foreground" />
                  Location
                </Label>
                <Input
                  id="location"
                  name="location"
                  placeholder="e.g., Nairobi, Kenya"
                  value={formData.location}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="h-12"
                  data-testid="location-input"
                />
              </div>

              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-muted-foreground" />
                  Member Since
                </Label>
                <Input
                  value={user?.created_at ? new Date(user.created_at).toLocaleDateString() : "N/A"}
                  disabled
                  className="h-12 bg-muted/50"
                />
              </div>

              {isEditing && (
                <div className="flex gap-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    className="flex-1 h-12"
                    onClick={() => {
                      setIsEditing(false);
                      setFormData({
                        name: user?.name || "",
                        phone: user?.phone || "",
                        location: user?.location || "",
                        profile_photo: user?.profile_photo || null
                      });
                    }}
                    data-testid="cancel-btn"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    className="flex-1 h-12 bg-primary hover:bg-primary/90"
                    disabled={loading}
                    data-testid="save-profile-btn"
                  >
                    {loading ? (
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Saving...
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <Save className="w-4 h-4" />
                        Save Changes
                      </div>
                    )}
                  </Button>
                </div>
              )}
            </form>
          </CardContent>
        </Card>

        {/* Quick Links */}
        <div className="mt-6 space-y-3">
          <Link to="/wallet">
            <Card className="border-border hover:bg-muted/50 transition-colors cursor-pointer">
              <CardContent className="p-4 flex items-center gap-4">
                <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center">
                  <Wallet className="w-5 h-5 text-primary" />
                </div>
                <div className="flex-1">
                  <p className="font-medium">My Wallet</p>
                  <p className="text-sm text-muted-foreground">Manage your balance and transactions</p>
                </div>
              </CardContent>
            </Card>
          </Link>
          <Link to="/client/bookings">
            <Card className="border-border hover:bg-muted/50 transition-colors cursor-pointer">
              <CardContent className="p-4 flex items-center gap-4">
                <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-accent" />
                </div>
                <div className="flex-1">
                  <p className="font-medium">My Bookings</p>
                  <p className="text-sm text-muted-foreground">View and manage your service bookings</p>
                </div>
              </CardContent>
            </Card>
          </Link>
        </div>
      </main>
    </div>
  );
}
