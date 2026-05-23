import { useEffect, useMemo, useRef, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { Dialog, DialogContent } from "./ui/dialog";
import { Button } from "./ui/button";
import { toast } from "sonner";
import { Download, Copy, Share2, Check, QrCode } from "lucide-react";

// Kazi Links gold (hsl(38, 92%, 50%))
const KAZI_GOLD = "#F5A524";
const KAZI_INK = "#1F1F23";

/**
 * Reusable QR share dialog. Renders a Kazi Links-branded QR code pointing to
 * the public professional profile URL. Supports download, copy-link, and
 * native share with graceful fallbacks.
 *
 * Props:
 *   open: boolean
 *   onOpenChange: (open: boolean) => void
 *   userId: string (required) — the professional's user id
 *   name?: string — display name to render under the QR
 *   profession?: string — sub-line
 *   rating?: number
 *   totalJobs?: number
 */
export default function ShareProfileQRDialog({
  open,
  onOpenChange,
  userId,
  name,
  profession,
  rating,
  totalJobs,
}) {
  const qrContainerRef = useRef(null);
  const [copied, setCopied] = useState(false);

  const profileUrl = useMemo(() => {
    if (!userId) return "";
    if (typeof window === "undefined") return `/professional/${userId}`;
    return `${window.location.origin}/professional/${userId}`;
  }, [userId]);

  useEffect(() => {
    if (!open) setCopied(false);
  }, [open]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(profileUrl);
      setCopied(true);
      toast.success("Profile link copied");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Could not copy link");
    }
  };

  const handleShare = async () => {
    const shareData = {
      title: `${name || "Kazi Links Professional"}`,
      text: `Book ${name || "this professional"} on Kazi Links`,
      url: profileUrl,
    };
    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (err) {
        if (err?.name !== "AbortError") {
          // Fallback: copy
          handleCopy();
        }
      }
    } else {
      handleCopy();
    }
  };

  /**
   * Render the dialog's QR card onto an off-screen canvas at high resolution,
   * then trigger a PNG download. Uses the SVG markup as the source so the QR
   * is crisp at any size.
   */
  const handleDownload = async () => {
    try {
      const svgEl = qrContainerRef.current?.querySelector("svg");
      if (!svgEl) {
        toast.error("Could not generate QR image");
        return;
      }
      const SCALE = 4;
      const card = await renderQRCardToPNG({
        svgEl,
        name: name || "Professional",
        profession: profession || "",
        rating,
        totalJobs,
        profileUrl,
        scale: SCALE,
      });

      const link = document.createElement("a");
      const safeName = (name || "kazi-links").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
      link.download = `${safeName || "kazi-links"}-qr.png`;
      link.href = card;
      link.click();
      toast.success("QR code downloaded");
    } catch (err) {
      toast.error("Download failed");
    }
  };

  if (!userId) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="sm:max-w-md p-0 overflow-hidden rounded-3xl"
        data-testid="share-profile-qr-dialog"
      >
        {/* Branded card — exact same layout as the rendered PNG */}
        <div
          ref={qrContainerRef}
          className="bg-gradient-to-br from-[#FFF7E6] via-[#FEFAF1] to-white p-6 sm:p-8"
        >
          {/* Brand bar */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <div
                className="w-9 h-9 rounded-xl flex items-center justify-center font-bold text-white text-lg"
                style={{ backgroundColor: KAZI_GOLD }}
              >
                K
              </div>
              <div>
                <p className="font-heading font-bold leading-tight" style={{ color: KAZI_INK }}>
                  Kazi Links
                </p>
                <p className="text-[10px] text-muted-foreground tracking-wider uppercase">
                  Book a Professional
                </p>
              </div>
            </div>
            <QrCode className="w-5 h-5" style={{ color: KAZI_GOLD }} />
          </div>

          {/* QR Code */}
          <div className="flex items-center justify-center">
            <div
              className="rounded-2xl p-4 sm:p-5 bg-white shadow-lg"
              style={{ border: `3px solid ${KAZI_GOLD}` }}
              data-testid="qr-code-container"
            >
              <QRCodeSVG
                value={profileUrl}
                size={220}
                bgColor="#FFFFFF"
                fgColor={KAZI_INK}
                level="H"
                marginSize={1}
                imageSettings={{
                  src:
                    "data:image/svg+xml;utf8," +
                    encodeURIComponent(
                      `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
                        <rect width='100' height='100' rx='22' fill='${KAZI_GOLD}'/>
                        <text x='50' y='66' text-anchor='middle'
                          font-family='Inter, system-ui, sans-serif'
                          font-size='58' font-weight='800' fill='white'>K</text>
                      </svg>`
                    ),
                  height: 40,
                  width: 40,
                  excavate: true,
                }}
              />
            </div>
          </div>

          {/* Pro details */}
          <div className="mt-5 text-center">
            <p className="font-heading font-bold text-lg" style={{ color: KAZI_INK }} data-testid="qr-pro-name">
              {name || "Professional"}
            </p>
            {profession && (
              <p className="text-sm text-muted-foreground mt-0.5">{profession}</p>
            )}
            {(rating != null || totalJobs != null) && (
              <div className="flex items-center justify-center gap-3 mt-3 text-xs text-muted-foreground">
                {rating != null && (
                  <span className="inline-flex items-center gap-1">
                    <span style={{ color: KAZI_GOLD }}>★</span>
                    {Number(rating).toFixed(1)}
                  </span>
                )}
                {totalJobs != null && totalJobs > 0 && (
                  <span>{totalJobs} jobs done</span>
                )}
              </div>
            )}
            <p className="text-[10px] text-muted-foreground mt-4 break-all px-3">
              Scan to book · {profileUrl.replace(/^https?:\/\//, "")}
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="p-4 sm:p-5 bg-card border-t border-border grid grid-cols-3 gap-2">
          <Button
            variant="outline"
            onClick={handleCopy}
            className="rounded-xl h-11"
            data-testid="qr-copy-link-btn"
          >
            {copied ? <Check className="w-4 h-4 mr-1.5" /> : <Copy className="w-4 h-4 mr-1.5" />}
            <span className="text-sm">{copied ? "Copied" : "Copy"}</span>
          </Button>
          <Button
            variant="outline"
            onClick={handleDownload}
            className="rounded-xl h-11"
            data-testid="qr-download-btn"
          >
            <Download className="w-4 h-4 mr-1.5" />
            <span className="text-sm">Save</span>
          </Button>
          <Button
            onClick={handleShare}
            className="rounded-xl h-11"
            style={{ backgroundColor: KAZI_GOLD, color: "white" }}
            data-testid="qr-share-btn"
          >
            <Share2 className="w-4 h-4 mr-1.5" />
            <span className="text-sm">Share</span>
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Render the QR + branded card to a high-resolution PNG data URL using a canvas.
 * Keeps the gold border, brand wordmark, and pro name in the saved image.
 */
async function renderQRCardToPNG({ svgEl, name, profession, rating, totalJobs, profileUrl, scale }) {
  // Card dimensions (in CSS px). Scaled for retina output.
  const W = 480;
  const H = 700;
  const canvas = document.createElement("canvas");
  canvas.width = W * scale;
  canvas.height = H * scale;
  const ctx = canvas.getContext("2d");
  ctx.scale(scale, scale);

  // Background gradient
  const bg = ctx.createLinearGradient(0, 0, W, H);
  bg.addColorStop(0, "#FFF7E6");
  bg.addColorStop(0.6, "#FEFAF1");
  bg.addColorStop(1, "#FFFFFF");
  ctx.fillStyle = bg;
  roundRect(ctx, 0, 0, W, H, 28);
  ctx.fill();

  // Brand row
  ctx.fillStyle = KAZI_GOLD;
  roundRect(ctx, 32, 32, 44, 44, 12);
  ctx.fill();
  ctx.fillStyle = "white";
  ctx.font = "bold 24px Inter, system-ui, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("K", 54, 54);
  ctx.fillStyle = KAZI_INK;
  ctx.textAlign = "left";
  ctx.textBaseline = "alphabetic";
  ctx.font = "bold 18px Inter, system-ui, sans-serif";
  ctx.fillText("Kazi Links", 88, 52);
  ctx.fillStyle = "#888";
  ctx.font = "10px Inter, system-ui, sans-serif";
  ctx.fillText("BOOK A PROFESSIONAL", 88, 68);

  // QR card box (gold border + white inner)
  const qrSize = 300;
  const qrBoxX = (W - qrSize - 40) / 2;
  const qrBoxY = 120;
  ctx.fillStyle = KAZI_GOLD;
  roundRect(ctx, qrBoxX, qrBoxY, qrSize + 40, qrSize + 40, 24);
  ctx.fill();
  ctx.fillStyle = "white";
  roundRect(ctx, qrBoxX + 6, qrBoxY + 6, qrSize + 28, qrSize + 28, 18);
  ctx.fill();

  // Inline-SVG → image for crisp draw
  const svgString = new XMLSerializer().serializeToString(svgEl);
  const img = await loadSvg(svgString);
  ctx.drawImage(img, qrBoxX + 20, qrBoxY + 20, qrSize, qrSize);

  // Pro name
  ctx.fillStyle = KAZI_INK;
  ctx.textAlign = "center";
  ctx.font = "bold 24px Inter, system-ui, sans-serif";
  ctx.fillText(truncate(name, 28), W / 2, qrBoxY + qrSize + 100);

  // Profession
  if (profession) {
    ctx.fillStyle = "#666";
    ctx.font = "15px Inter, system-ui, sans-serif";
    ctx.fillText(truncate(profession, 36), W / 2, qrBoxY + qrSize + 124);
  }

  // Stats line
  const statsParts = [];
  if (rating != null) statsParts.push(`★ ${Number(rating).toFixed(1)}`);
  if (totalJobs != null && totalJobs > 0) statsParts.push(`${totalJobs} jobs done`);
  if (statsParts.length) {
    ctx.fillStyle = "#777";
    ctx.font = "13px Inter, system-ui, sans-serif";
    ctx.fillText(statsParts.join("  ·  "), W / 2, qrBoxY + qrSize + 150);
  }

  // Footer URL
  ctx.fillStyle = "#999";
  ctx.font = "11px Inter, system-ui, sans-serif";
  ctx.fillText(
    "Scan to book · " + truncate(profileUrl.replace(/^https?:\/\//, ""), 50),
    W / 2,
    H - 32
  );

  return canvas.toDataURL("image/png");
}

function loadSvg(svgString) {
  return new Promise((resolve, reject) => {
    const blob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve(img);
    };
    img.onerror = (e) => {
      URL.revokeObjectURL(url);
      reject(e);
    };
    img.src = url;
  });
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function truncate(s, max) {
  if (!s) return "";
  return s.length > max ? s.slice(0, max - 1) + "…" : s;
}
