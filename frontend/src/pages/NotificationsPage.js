import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Switch } from "../components/ui/switch";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { 
  ArrowLeft, Bell, BellOff, Briefcase, CheckCircle2, 
  Clock, AlertCircle, Trash2
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function NotificationsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pushEnabled, setPushEnabled] = useState(false);

  useEffect(() => {
    fetchNotifications();
    checkPushPermission();
  }, []);

  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/notifications`);
      setNotifications(response.data);
    } catch (error) {
      console.error("Failed to fetch notifications:", error);
    } finally {
      setLoading(false);
    }
  };

  const checkPushPermission = () => {
    if ('Notification' in window) {
      setPushEnabled(Notification.permission === 'granted');
    }
  };

  const handleEnablePush = async () => {
    if (!("Notification" in window) || !("serviceWorker" in navigator) || !("PushManager" in window)) {
      toast.error("Push notifications are not supported in this browser");
      return;
    }

    try {
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        toast.error("Permission denied for notifications");
        return;
      }

      const registration = await navigator.serviceWorker.ready;
      let subscription = await registration.pushManager.getSubscription();

      // VAPID public key (optional). If not configured server-side, fall back to a
      // local subscription stub so the user still gets in-app toast notifications.
      const vapidKey = process.env.REACT_APP_VAPID_PUBLIC_KEY;
      if (!subscription && vapidKey) {
        try {
          subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(vapidKey),
          });
        } catch (subErr) {
          console.warn("PushManager.subscribe failed — falling back to stub:", subErr);
        }
      }

      const payload = subscription
        ? subscription.toJSON()
        : {
            endpoint: `local-${user?.id}-${Date.now()}`,
            keys: { p256dh: "local", auth: "local" },
          };

      await axios.post(`${API}/notifications/subscribe`, {
        endpoint: payload.endpoint,
        keys: payload.keys || { p256dh: "", auth: "" },
      });
      try {
        localStorage.setItem("kazi_push_endpoint", payload.endpoint);
      } catch { /* ignore */ }

      setPushEnabled(true);
      toast.success("Push notifications enabled!");
    } catch (error) {
      console.error("Failed to enable push:", error);
      toast.error("Failed to enable notifications");
    }
  };

  const handleDisablePush = async () => {
    try {
      let endpoint = null;
      try {
        endpoint = localStorage.getItem("kazi_push_endpoint");
      } catch { /* ignore */ }
      if (!endpoint && "serviceWorker" in navigator) {
        try {
          const reg = await navigator.serviceWorker.ready;
          const sub = await reg.pushManager.getSubscription();
          if (sub) {
            endpoint = sub.endpoint;
            await sub.unsubscribe().catch(() => null);
          }
        } catch { /* ignore */ }
      }
      if (endpoint) {
        await axios.delete(`${API}/notifications/unsubscribe?endpoint=${encodeURIComponent(endpoint)}`);
      }
      try { localStorage.removeItem("kazi_push_endpoint"); } catch { /* ignore */ }
      setPushEnabled(false);
      toast.success("Push notifications disabled");
    } catch (error) {
      console.error("Failed to disable push:", error);
    }
  };

  // Convert VAPID base64 URL-safe key to Uint8Array required by PushManager.subscribe
  function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    const rawData = atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
    return outputArray;
  }

  const handleMarkRead = async (notificationId) => {
    try {
      await axios.put(`${API}/notifications/${notificationId}/read`);
      setNotifications(notifications.map(n => 
        n.id === notificationId ? {...n, read: true} : n
      ));
    } catch (error) {
      console.error("Failed to mark as read:", error);
    }
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case "new_job":
        return <Briefcase className="w-5 h-5 text-primary" />;
      case "bid_accepted":
        return <CheckCircle2 className="w-5 h-5 text-green-600" />;
      default:
        return <Bell className="w-5 h-5 text-muted-foreground" />;
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-20 lg:pb-0" data-testid="notifications-page">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-border/40">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => navigate(-1)} className="p-2 hover:bg-muted rounded-lg">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="font-heading font-semibold">Notifications</h1>
            {unreadCount > 0 && (
              <Badge className="bg-primary">{unreadCount} new</Badge>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6">
        {/* Push Notification Settings */}
        <Card className="border-border mb-6" data-testid="push-settings">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  pushEnabled ? "bg-primary/10" : "bg-muted"
                }`}>
                  {pushEnabled ? (
                    <Bell className="w-5 h-5 text-primary" />
                  ) : (
                    <BellOff className="w-5 h-5 text-muted-foreground" />
                  )}
                </div>
                <div>
                  <p className="font-medium">Push Notifications</p>
                  <p className="text-sm text-muted-foreground">
                    {pushEnabled 
                      ? "You'll receive alerts for new jobs and booking updates"
                      : "Enable to get instant alerts"
                    }
                  </p>
                </div>
              </div>
              <Switch
                checked={pushEnabled}
                onCheckedChange={(checked) => checked ? handleEnablePush() : handleDisablePush()}
                data-testid="push-toggle"
              />
            </div>
          </CardContent>
        </Card>

        {/* Notification Types Info */}
        {user?.role === "professional" && (
          <div className="grid grid-cols-2 gap-4 mb-6">
            <Card className="border-border">
              <CardContent className="p-4 text-center">
                <Briefcase className="w-8 h-8 text-primary mx-auto mb-2" />
                <p className="font-medium text-sm">New Jobs</p>
                <p className="text-xs text-muted-foreground">Jobs matching your skills</p>
              </CardContent>
            </Card>
            <Card className="border-border">
              <CardContent className="p-4 text-center">
                <CheckCircle2 className="w-8 h-8 text-green-600 mx-auto mb-2" />
                <p className="font-medium text-sm">Bid Accepted</p>
                <p className="text-xs text-muted-foreground">When clients accept your bid</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Notifications List */}
        <Card className="border-border" data-testid="notifications-list">
          <CardHeader>
            <CardTitle className="font-heading text-lg">Recent Notifications</CardTitle>
          </CardHeader>
          <CardContent>
            {notifications.length > 0 ? (
              <div className="space-y-3">
                {notifications.map((notification) => (
                  <div 
                    key={notification.id}
                    className={`flex items-start gap-4 p-4 rounded-xl cursor-pointer transition-colors ${
                      notification.read ? "bg-muted/30" : "bg-primary/5 border border-primary/20"
                    }`}
                    onClick={() => !notification.read && handleMarkRead(notification.id)}
                    data-testid={`notification-${notification.id}`}
                  >
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                      notification.read ? "bg-muted" : "bg-primary/10"
                    }`}>
                      {getNotificationIcon(notification.data?.type)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className={`font-medium ${notification.read ? "text-muted-foreground" : ""}`}>
                            {notification.title}
                          </p>
                          <p className="text-sm text-muted-foreground">{notification.body}</p>
                        </div>
                        {!notification.read && (
                          <div className="w-2 h-2 bg-primary rounded-full flex-shrink-0 mt-2" />
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground mt-2">
                        {new Date(notification.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Bell className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">No notifications yet</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {user?.role === "professional" 
                    ? "You'll be notified when new jobs are posted"
                    : "You'll be notified about your booking updates"
                  }
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
