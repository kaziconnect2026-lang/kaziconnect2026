import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * Kazi Links brand logo. Clicking navigates to the user's dashboard
 * (role-based) or the public landing page for guests.
 *
 * Props:
 *   size:  "sm" (w-8/rounded-lg)  |  "md" (default, w-10/rounded-xl)
 *   label: React node rendered next to the icon. Pass `null` for icon-only.
 */
export default function KaziLogo({ size = "md", label = "Kazi Links", subtitle, className = "" }) {
  const { user } = useAuth();

  const dashboardHref =
    user?.role === "client"
      ? "/client"
      : user?.role === "professional"
        ? "/professional"
        : user?.role === "admin"
          ? "/admin"
          : "/";

  const isSmall = size === "sm";
  const imgClass = isSmall
    ? "w-8 h-8 rounded-lg object-cover shrink-0"
    : "w-10 h-10 rounded-xl object-cover shrink-0";
  const labelClass = isSmall
    ? "font-heading font-bold"
    : "font-heading font-bold text-xl";

  return (
    <Link
      to={dashboardHref}
      className={`flex items-center gap-2 hover:opacity-90 transition-opacity ${className}`}
      data-testid="kazi-logo-link"
      aria-label="Kazi Links home"
    >
      <img src="/logo.png" alt="Kazi Links" className={imgClass} />
      {label !== null && (
        subtitle ? (
          <div className="min-w-0">
            <span className={labelClass}>{label}</span>
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          </div>
        ) : (
          <span className={`${labelClass} text-foreground`}>{label}</span>
        )
      )}
    </Link>
  );
}
