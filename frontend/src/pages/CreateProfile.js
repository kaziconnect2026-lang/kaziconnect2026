import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { ArrowLeft, Plus, X, Camera, User } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function CreateProfile() {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [existingProfile, setExistingProfile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [formData, setFormData] = useState({
    profession: "",
    bio: "",
    skills: [],
    hourly_rate: "",
    project_rate_min: "",
    project_rate_max: "",
    pricing_type: "both",
    experience_years: "",
    portfolio_images: [],
    id_number: ""
  });
  const [newSkill, setNewSkill] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [categoriesRes] = await Promise.all([
          axios.get(`${API}/categories/grouped`)
        ]);
        setCategories(categoriesRes.data);
        
        // Set user profile photo if exists
        if (user?.profile_photo) {
          setPhotoPreview(user.profile_photo);
        }
        
        // Try to fetch existing profile
        try {
          const profileRes = await axios.get(`${API}/professionals/profile`);
          setExistingProfile(profileRes.data);
          setFormData({
            profession: profileRes.data.profession || "",
            bio: profileRes.data.bio || "",
            skills: profileRes.data.skills || [],
            hourly_rate: profileRes.data.hourly_rate?.toString() || "",
            project_rate_min: profileRes.data.project_rate_min?.toString() || "",
            project_rate_max: profileRes.data.project_rate_max?.toString() || "",
            pricing_type: profileRes.data.pricing_type || "both",
            experience_years: profileRes.data.experience_years?.toString() || "",
            portfolio_images: profileRes.data.portfolio_images || [],
            id_number: profileRes.data.id_number || ""
          });
        } catch (error) {
          // No existing profile, that's fine
        }
      } catch (error) {
        console.error("Failed to fetch data:", error);
      }
    };
    fetchData();
  }, [user]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
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
      toast.success("Profile photo updated!");
      if (refreshUser) refreshUser();
    } catch (error) {
      toast.error("Failed to upload photo");
      setPhotoPreview(user?.profile_photo || null);
    } finally {
      setUploadingPhoto(false);
    }
  };

  const addSkill = () => {
    if (newSkill.trim() && !formData.skills.includes(newSkill.trim())) {
      setFormData({ ...formData, skills: [...formData.skills, newSkill.trim()] });
      setNewSkill("");
    }
  };

  const removeSkill = (skillToRemove) => {
    setFormData({ 
      ...formData, 
      skills: formData.skills.filter(skill => skill !== skillToRemove) 
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        profession: formData.profession,
        bio: formData.bio,
        skills: formData.skills,
        hourly_rate: formData.hourly_rate ? parseFloat(formData.hourly_rate) : null,
        project_rate_min: formData.project_rate_min ? parseFloat(formData.project_rate_min) : null,
        project_rate_max: formData.project_rate_max ? parseFloat(formData.project_rate_max) : null,
        pricing_type: formData.pricing_type,
        experience_years: parseInt(formData.experience_years) || 0,
        portfolio_images: formData.portfolio_images,
        id_number: formData.id_number || null
      };

      if (existingProfile) {
        await axios.put(`${API}/professionals/profile`, payload);
        toast.success("Profile updated successfully!");
      } else {
        await axios.post(`${API}/professionals/profile`, payload);
        toast.success("Profile created successfully!");
      }
      
      navigate("/professional");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save profile");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background" data-testid="create-profile-page">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-border/40">
        <div className="max-w-2xl mx-auto px-4 h-16 flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-muted rounded-lg">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="font-heading font-semibold">
            {existingProfile ? "Edit Profile" : "Create Your Profile"}
          </h1>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-6">
        <Card className="border-border">
          <CardHeader>
            <CardTitle className="font-heading">Professional Information</CardTitle>
            <p className="text-sm text-muted-foreground">
              Set up your profile to start receiving bookings from clients
            </p>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Profile Photo Section */}
              <div className="flex flex-col items-center pb-6 border-b border-border">
                <div className="relative">
                  <div className="w-28 h-28 bg-muted rounded-full flex items-center justify-center overflow-hidden border-4 border-background shadow-lg">
                    {photoPreview ? (
                      <img 
                        src={photoPreview} 
                        alt="Profile" 
                        className="w-full h-full object-cover"
                        data-testid="profile-photo-preview"
                      />
                    ) : (
                      <User className="w-12 h-12 text-muted-foreground" />
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="absolute bottom-0 right-0 w-9 h-9 bg-primary rounded-full flex items-center justify-center text-primary-foreground shadow-lg hover:bg-primary/90 transition-colors"
                    disabled={uploadingPhoto}
                    data-testid="upload-photo-btn"
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
                    data-testid="photo-file-input"
                  />
                </div>
                <p className="text-sm text-muted-foreground mt-3">
                  {photoPreview ? "Tap to change photo" : "Add a profile photo"}
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="profession">Profession</Label>
                <Select 
                  value={formData.profession} 
                  onValueChange={(value) => setFormData({...formData, profession: value})}
                >
                  <SelectTrigger className="h-12" data-testid="profession-select">
                    <SelectValue placeholder="Select your profession" />
                  </SelectTrigger>
                  <SelectContent className="max-h-80">
                    {Object.entries(categories).map(([groupName, groupCats]) => (
                      <div key={groupName}>
                        <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground bg-muted/50 sticky top-0">
                          {groupName}
                        </div>
                        {groupCats.map((cat) => (
                          <SelectItem key={cat.id} value={cat.name}>{cat.name}</SelectItem>
                        ))}
                      </div>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="bio">Bio</Label>
                <Textarea
                  id="bio"
                  name="bio"
                  placeholder="Tell clients about yourself and your work..."
                  value={formData.bio}
                  onChange={handleChange}
                  required
                  rows={4}
                  data-testid="bio-input"
                />
              </div>

              <div className="space-y-2">
                <Label>Skills</Label>
                <div className="flex gap-2">
                  <Input
                    placeholder="Add a skill"
                    value={newSkill}
                    onChange={(e) => setNewSkill(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && (e.preventDefault(), addSkill())}
                    className="h-10"
                    data-testid="skill-input"
                  />
                  <Button type="button" onClick={addSkill} variant="outline" size="icon">
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
                  {formData.skills.map((skill, i) => (
                    <span 
                      key={i} 
                      className="inline-flex items-center gap-1 px-3 py-1 bg-primary/10 text-primary rounded-full text-sm"
                    >
                      {skill}
                      <button type="button" onClick={() => removeSkill(skill)}>
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <Label>Pricing Type</Label>
                <Select 
                  value={formData.pricing_type} 
                  onValueChange={(value) => setFormData({...formData, pricing_type: value})}
                >
                  <SelectTrigger className="h-12" data-testid="pricing-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="hourly">Hourly Only</SelectItem>
                    <SelectItem value="project">Project Only</SelectItem>
                    <SelectItem value="both">Both Hourly & Project</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {(formData.pricing_type === "hourly" || formData.pricing_type === "both") && (
                <div className="space-y-2">
                  <Label htmlFor="hourly_rate">Hourly Rate (KSh)</Label>
                  <Input
                    id="hourly_rate"
                    name="hourly_rate"
                    type="number"
                    placeholder="e.g., 500"
                    value={formData.hourly_rate}
                    onChange={handleChange}
                    className="h-12"
                    data-testid="hourly-rate-input"
                  />
                </div>
              )}

              {(formData.pricing_type === "project" || formData.pricing_type === "both") && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="project_rate_min">Min Project Rate (KSh)</Label>
                    <Input
                      id="project_rate_min"
                      name="project_rate_min"
                      type="number"
                      placeholder="e.g., 2000"
                      value={formData.project_rate_min}
                      onChange={handleChange}
                      className="h-12"
                      data-testid="project-rate-min-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="project_rate_max">Max Project Rate (KSh)</Label>
                    <Input
                      id="project_rate_max"
                      name="project_rate_max"
                      type="number"
                      placeholder="e.g., 10000"
                      value={formData.project_rate_max}
                      onChange={handleChange}
                      className="h-12"
                      data-testid="project-rate-max-input"
                    />
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="experience_years">Years of Experience</Label>
                <Input
                  id="experience_years"
                  name="experience_years"
                  type="number"
                  placeholder="e.g., 5"
                  value={formData.experience_years}
                  onChange={handleChange}
                  required
                  className="h-12"
                  data-testid="experience-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="id_number">National ID Number</Label>
                <Input
                  id="id_number"
                  name="id_number"
                  type="text"
                  placeholder="e.g., 12345678"
                  value={formData.id_number}
                  onChange={handleChange}
                  className="h-12"
                  data-testid="id-number-input"
                />
                <p className="text-xs text-muted-foreground">
                  Your ID is used for verification purposes and helps build trust with clients
                </p>
              </div>

              <Button 
                type="submit" 
                className="w-full h-12 rounded-xl bg-primary hover:bg-primary/90"
                disabled={loading}
                data-testid="save-profile-btn"
              >
                {loading ? "Saving..." : (existingProfile ? "Update Profile" : "Create Profile")}
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
