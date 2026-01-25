import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";
import { AuthProvider, useAuth } from "./context/AuthContext";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ClientDashboard from "./pages/ClientDashboard";
import ProfessionalDashboard from "./pages/ProfessionalDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import SearchProfessionals from "./pages/SearchProfessionals";
import ProfessionalProfile from "./pages/ProfessionalProfile";
import PostJob from "./pages/PostJob";
import CreateProfile from "./pages/CreateProfile";
import Bookings from "./pages/Bookings";
import AvailableJobs from "./pages/AvailableJobs";
import MyBids from "./pages/MyBids";
import JobBids from "./pages/JobBids";
import "./App.css";

// Protected Route Component
const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // Redirect to appropriate dashboard
    if (user.role === "client") return <Navigate to="/client" replace />;
    if (user.role === "professional") return <Navigate to="/professional" replace />;
    if (user.role === "admin") return <Navigate to="/admin" replace />;
  }
  
  return children;
};

// Public Route - redirect if logged in
const PublicRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }
  
  if (user) {
    if (user.role === "client") return <Navigate to="/client" replace />;
    if (user.role === "professional") return <Navigate to="/professional" replace />;
    if (user.role === "admin") return <Navigate to="/admin" replace />;
  }
  
  return children;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="App min-h-screen bg-background">
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
            <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
            
            {/* Client Routes */}
            <Route path="/client" element={
              <ProtectedRoute allowedRoles={["client"]}>
                <ClientDashboard />
              </ProtectedRoute>
            } />
            <Route path="/search" element={
              <ProtectedRoute allowedRoles={["client"]}>
                <SearchProfessionals />
              </ProtectedRoute>
            } />
            <Route path="/post-job" element={
              <ProtectedRoute allowedRoles={["client"]}>
                <PostJob />
              </ProtectedRoute>
            } />
            <Route path="/professional/:id" element={
              <ProtectedRoute allowedRoles={["client"]}>
                <ProfessionalProfile />
              </ProtectedRoute>
            } />
            <Route path="/client/bookings" element={
              <ProtectedRoute allowedRoles={["client"]}>
                <Bookings />
              </ProtectedRoute>
            } />
            <Route path="/client/jobs/:jobId/bids" element={
              <ProtectedRoute allowedRoles={["client"]}>
                <JobBids />
              </ProtectedRoute>
            } />
            
            {/* Professional Routes */}
            <Route path="/professional" element={
              <ProtectedRoute allowedRoles={["professional"]}>
                <ProfessionalDashboard />
              </ProtectedRoute>
            } />
            <Route path="/create-profile" element={
              <ProtectedRoute allowedRoles={["professional"]}>
                <CreateProfile />
              </ProtectedRoute>
            } />
            <Route path="/professional/bookings" element={
              <ProtectedRoute allowedRoles={["professional"]}>
                <Bookings />
              </ProtectedRoute>
            } />
            <Route path="/professional/jobs" element={
              <ProtectedRoute allowedRoles={["professional"]}>
                <AvailableJobs />
              </ProtectedRoute>
            } />
            <Route path="/professional/bids" element={
              <ProtectedRoute allowedRoles={["professional"]}>
                <MyBids />
              </ProtectedRoute>
            } />
            
            {/* Admin Routes */}
            <Route path="/admin" element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <AdminDashboard />
              </ProtectedRoute>
            } />
            
            {/* Catch all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <Toaster position="top-right" richColors />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
