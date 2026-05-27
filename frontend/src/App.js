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
import WalletPage from "./pages/WalletPage";
import NotificationsPage from "./pages/NotificationsPage";
import LedgerPage from "./pages/LedgerPage";
import ClientProfile from "./pages/ClientProfile";
import MessagesPage from "./pages/MessagesPage";
import ChatThreadPage from "./pages/ChatThreadPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import AdminConversationsPage from "./pages/AdminConversationsPage";
import AdminKycPage from "./pages/AdminKycPage";
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
            <Route path="/forgot-password" element={<PublicRoute><ForgotPasswordPage /></PublicRoute>} />
            <Route path="/reset-password" element={<PublicRoute><ResetPasswordPage /></PublicRoute>} />
            
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
            <Route path="/client/profile" element={
              <ProtectedRoute allowedRoles={["client"]}>
                <ClientProfile />
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
            
            {/* Shared Routes (both client and professional) */}
            <Route path="/wallet" element={
              <ProtectedRoute allowedRoles={["client", "professional"]}>
                <WalletPage />
              </ProtectedRoute>
            } />
            <Route path="/notifications" element={
              <ProtectedRoute allowedRoles={["client", "professional"]}>
                <NotificationsPage />
              </ProtectedRoute>
            } />
            <Route path="/messages" element={
              <ProtectedRoute allowedRoles={["client", "professional"]}>
                <MessagesPage />
              </ProtectedRoute>
            } />
            <Route path="/messages/:conversationId" element={
              <ProtectedRoute allowedRoles={["client", "professional"]}>
                <ChatThreadPage />
              </ProtectedRoute>
            } />
            
            {/* Admin Routes */}
            <Route path="/admin" element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <AdminDashboard />
              </ProtectedRoute>
            } />
            <Route path="/admin/ledger" element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <LedgerPage />
              </ProtectedRoute>
            } />
            <Route path="/admin/conversations" element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <AdminConversationsPage />
              </ProtectedRoute>
            } />
            <Route path="/admin/conversations/:conversationId" element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <AdminConversationsPage />
              </ProtectedRoute>
            } />
            <Route path="/admin/kyc" element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <AdminKycPage />
              </ProtectedRoute>
            } />
            <Route path="/admin/kyc/:userId" element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <AdminKycPage />
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
