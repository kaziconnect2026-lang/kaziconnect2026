import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { Card, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { toast } from "sonner";
import { ShieldCheck, Upload, Loader2, Camera, CheckCircle2, AlertTriangle, RotateCw } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * ID Photo Verification Card.
 * Both sides of national ID are required. Uses object-storage backed
 * POST /api/kyc/upload-id and reflects status from GET /api/kyc/status.
 */
export default function IdVerificationCard() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploadingSide, setUploadingSide] = useState(null);
  const [previews, setPreviews] = useState({ front: null, back: null });
  const frontRef = useRef(null);
  const backRef = useRef(null);

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/kyc/status`);
      setStatus(res.data);
      // Load previews via authed blob fetch (so the <img> can render auth-gated files)
      if (res.data.id_front_url) loadAuthedImage(res.data.id_front_url, "front");
      if (res.data.id_back_url) loadAuthedImage(res.data.id_back_url, "back");
    } catch (err) {
      console.error("Failed to fetch KYC status:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadAuthedImage = async (url, key) => {
    try {
      const fullUrl = url.startsWith("http") ? url : `${BACKEND_URL}${url}`;
      const r = await axios.get(fullUrl, { responseType: "blob" });
      const blobUrl = URL.createObjectURL(r.data);
      setPreviews((p) => ({ ...p, [key]: blobUrl }));
    } catch {
      /* ignore — preview is best-effort */
    }
  };

  const handleFileChange = async (e, side) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      toast.error("Please upload an image (.jpg, .png, .webp)");
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      toast.error("File too large — max 8 MB");
      return;
    }
    setUploadingSide(side);
    try {
      const form = new FormData();
      form.append("side", side);
      form.append("file", file);
      const res = await axios.post(`${API}/kyc/upload-id`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success(`${side === "front" ? "Front" : "Back"} of ID uploaded`);
      // Show preview from the just-picked local file (faster than re-fetching)
      setPreviews((p) => ({ ...p, [side]: URL.createObjectURL(file) }));
      // Refresh status so re-uploads reset verification
      setStatus((prev) => ({
        ...(prev || {}),
        [side === "front" ? "id_front_uploaded" : "id_back_uploaded"]: true,
        [side === "front" ? "id_front_url" : "id_back_url"]: res.data.url,
        id_verified: false,
        id_verification_status: "pending",
      }));
    } catch (err) {
      toast.error(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploadingSide(null);
      // Reset input so re-picking the same file still fires onChange
      if (e.target) e.target.value = "";
    }
  };

  const renderSide = (side, label, inputRef) => {
    const isUploaded = side === "front" ? status?.id_front_uploaded : status?.id_back_uploaded;
    const preview = previews[side];
    const isUploading = uploadingSide === side;
    return (
      <div
        className="space-y-2"
        data-testid={`kyc-${side}-block`}
      >
        <p className="text-sm font-medium flex items-center gap-2">
          {label}
          {isUploaded && (
            <Badge className="bg-green-100 text-green-800 border-0 text-[10px] gap-1">
              <CheckCircle2 className="w-3 h-3" /> Uploaded
            </Badge>
          )}
        </p>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={isUploading}
          className={`w-full aspect-[16/10] rounded-xl border-2 border-dashed transition-colors flex items-center justify-center overflow-hidden relative ${
            preview ? "border-primary/40 bg-card" : "border-border bg-muted/30 hover:border-primary/40 hover:bg-primary/5"
          }`}
          data-testid={`kyc-${side}-button`}
        >
          {preview ? (
            <>
              <img src={preview} alt={`${label} preview`} className="w-full h-full object-cover" />
              <div className="absolute inset-x-0 bottom-0 bg-black/60 text-white text-xs py-1.5 px-2 flex items-center justify-center gap-1">
                <RotateCw className="w-3 h-3" /> Tap to replace
              </div>
            </>
          ) : isUploading ? (
            <div className="flex flex-col items-center gap-2 text-muted-foreground">
              <Loader2 className="w-6 h-6 animate-spin" />
              <span className="text-xs">Uploading…</span>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 text-muted-foreground">
              <Camera className="w-6 h-6" />
              <span className="text-xs">Tap to capture or upload</span>
            </div>
          )}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          capture="environment"
          onChange={(e) => handleFileChange(e, side)}
          className="hidden"
          data-testid={`kyc-${side}-input`}
        />
      </div>
    );
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6 flex items-center justify-center text-muted-foreground">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading verification status…
        </CardContent>
      </Card>
    );
  }

  const isVerified = !!status?.id_verified;
  const isPending = status?.id_verification_status === "pending" &&
    status?.id_front_uploaded && status?.id_back_uploaded;
  const isRejected = status?.id_verification_status === "rejected";

  return (
    <Card className="border-border overflow-hidden" data-testid="id-verification-card">
      <CardContent className="p-5 sm:p-6 space-y-4">
        <div className="flex items-start gap-3">
          <div className="w-11 h-11 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-5 h-5 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-heading font-semibold text-base">ID Verification</h3>
              {isVerified && (
                <Badge className="bg-green-100 text-green-800 border-0 gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Verified
                </Badge>
              )}
              {isPending && !isVerified && (
                <Badge className="bg-amber-100 text-amber-900 border-0">
                  Under review
                </Badge>
              )}
              {isRejected && (
                <Badge className="bg-red-100 text-red-800 border-0 gap-1">
                  <AlertTriangle className="w-3 h-3" /> Re-upload needed
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              {isVerified
                ? "Your ID has been verified. Clients see a trust badge on your profile."
                : "Upload clear photos of the front and back of your national ID. We use this to build trust and prevent fraud."}
            </p>
            {isRejected && status?.id_verification_notes && (
              <p className="text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg px-2 py-1.5 mt-2">
                Admin note: {status.id_verification_notes}
              </p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {renderSide("front", "Front of ID", frontRef)}
          {renderSide("back", "Back of ID", backRef)}
        </div>

        <div className="text-xs text-muted-foreground bg-muted/40 rounded-lg p-3 flex items-start gap-2">
          <Upload className="w-4 h-4 mt-0.5 text-primary shrink-0" />
          <span>
            We accept JPG, PNG, or WEBP up to 8 MB per side. Your ID is encrypted at rest and only
            visible to verified Kazi Links admins for the purpose of confirming your identity.
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
