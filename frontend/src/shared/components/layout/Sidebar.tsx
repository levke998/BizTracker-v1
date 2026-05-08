import { NavLink, useLocation } from "react-router-dom";

import { useCurrentUser, useLogout } from "../../../modules/identity/hooks/useLogin";
import { routes } from "../../constants/routes";
import { Button } from "../ui/Button";

type IconName =
  | "activity"
  | "barChart"
  | "book"
  | "calendar"
  | "box"
  | "cash"
  | "database"
  | "file"
  | "receipt"
  | "shopping"
  | "upload";

type NavigationItem = {
  to: string;
  label: string;
  icon: IconName;
};

const primaryNavigation: NavigationItem[] = [
  { to: routes.dashboard, label: "Dashboard", icon: "barChart" },
  { to: routes.imports, label: "Import központ", icon: "upload" },
];

const eventNavigation: NavigationItem[] = [
  { to: routes.eventsNew, label: "Új esemény", icon: "calendar" },
  { to: routes.eventsAnalytics, label: "Esemény elemző", icon: "barChart" },
];

const catalogNavigation: NavigationItem[] = [
  { to: routes.catalogProducts, label: "Termékek", icon: "box" },
  { to: routes.catalogIngredients, label: "Alapanyagok", icon: "book" },
  { to: routes.productionRecipes, label: "Recept readiness", icon: "receipt" },
];

const procurementNavigation: NavigationItem[] = [
  { to: routes.procurementSuppliers, label: "Beszállítók", icon: "shopping" },
  { to: routes.procurementInvoices, label: "Beszerzési számlák", icon: "file" },
];

const supportNavigation: NavigationItem[] = [
  { to: routes.masterData, label: "Törzsadatok", icon: "database" },
  { to: routes.demoPos, label: "Demo kassza", icon: "cash" },
];

function Icon({ name }: { name: IconName }) {
  const common = {
    fill: "none",
    stroke: "currentColor",
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    strokeWidth: 2,
    viewBox: "0 0 24 24",
  };

  const paths: Record<IconName, JSX.Element> = {
    activity: <path d="M22 12h-4l-3 9L9 3l-3 9H2" />,
    barChart: (
      <>
        <path d="M3 3v18h18" />
        <path d="M8 17V9" />
        <path d="M13 17V5" />
        <path d="M18 17v-6" />
      </>
    ),
    calendar: (
      <>
        <rect x="3" y="4" width="18" height="18" rx="2" />
        <path d="M16 2v4M8 2v4M3 10h18" />
      </>
    ),
    book: (
      <>
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
        <path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5z" />
      </>
    ),
    box: (
      <>
        <path d="M21 8 12 3 3 8l9 5 9-5Z" />
        <path d="m3 8 9 5v8l9-5V8" />
      </>
    ),
    cash: (
      <>
        <rect x="3" y="6" width="18" height="12" rx="2" />
        <circle cx="12" cy="12" r="2" />
        <path d="M7 12h.01M17 12h.01" />
      </>
    ),
    database: (
      <>
        <ellipse cx="12" cy="5" rx="8" ry="3" />
        <path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5" />
        <path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6" />
      </>
    ),
    file: (
      <>
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
        <path d="M14 2v6h6" />
      </>
    ),
    receipt: (
      <>
        <path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z" />
        <path d="M8 8h8M8 12h8M8 16h5" />
      </>
    ),
    shopping: (
      <>
        <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z" />
        <path d="M3 6h18" />
        <path d="M16 10a4 4 0 0 1-8 0" />
      </>
    ),
    upload: (
      <>
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <path d="m17 8-5-5-5 5" />
        <path d="M12 3v12" />
      </>
    ),
  };

  return (
    <svg className="sidebar-icon" aria-hidden="true" {...common}>
      {paths[name]}
    </svg>
  );
}

function NavigationLink({
  item,
  onNavigate,
}: {
  item: NavigationItem;
  onNavigate: () => void;
}) {
  return (
    <NavLink
      to={item.to}
      title={item.label}
      onClick={onNavigate}
      className={({ isActive }) =>
        isActive ? "sidebar-link sidebar-link-active" : "sidebar-link"
      }
    >
      <Icon name={item.icon} />
      <span>{item.label}</span>
    </NavLink>
  );
}

export function Sidebar({
  collapsed,
  onToggleCollapsed,
  onNavigate,
}: {
  collapsed: boolean;
  onToggleCollapsed: () => void;
  onNavigate: () => void;
}) {
  const location = useLocation();
  const currentUser = useCurrentUser();
  const logout = useLogout();
  const formattedDate = new Intl.DateTimeFormat("hu-HU", {
    year: "numeric",
    month: "long",
    day: "2-digit",
  }).format(new Date());
  const eventsIsActive = location.pathname.startsWith("/events");
  const catalogIsActive =
    location.pathname.startsWith("/catalog") ||
    location.pathname.startsWith("/production");
  const procurementIsActive = location.pathname.startsWith("/procurement");

  return (
    <aside className={collapsed ? "sidebar sidebar-collapsed" : "sidebar"}>
      <div className="sidebar-brand">
        <div className="brand-logo">
          <span className="brand-logo-icon">
            <Icon name="activity" />
          </span>
          <span className="sidebar-brand-title">BizTracker</span>
          <button
            type="button"
            className="sidebar-toggle-button"
            onClick={onToggleCollapsed}
            aria-label={collapsed ? "Oldalsáv megnyitása" : "Oldalsáv bezárása"}
            title={collapsed ? "Oldalsáv megnyitása" : "Oldalsáv bezárása"}
          >
            {collapsed ? "›" : "‹"}
          </button>
        </div>
        <span className="sidebar-brand-subtitle">
          Üzleti iránytű két vállalkozáshoz
        </span>
      </div>

      <div className="sidebar-profile">
        <span>{formattedDate}</span>
        {currentUser.data ? <strong>{currentUser.data.full_name}</strong> : null}
        <Button variant="secondary" className="sidebar-logout-button" onClick={logout}>
          Kilépés
        </Button>
      </div>

      <div className="sidebar-section">
        <span className="sidebar-section-label">Menü</span>
        <nav className="sidebar-nav">
          {primaryNavigation.map((item) => (
            <NavigationLink item={item} key={item.to} onNavigate={onNavigate} />
          ))}

          <details className="sidebar-group" open={!collapsed && eventsIsActive}>
            <summary title="Események">
              <Icon name="calendar" />
              <span>Események</span>
            </summary>
            <div className="sidebar-group-links">
              {eventNavigation.map((item) => (
                <NavigationLink item={item} key={item.to} onNavigate={onNavigate} />
              ))}
            </div>
          </details>

          <details className="sidebar-group" open={!collapsed && catalogIsActive}>
            <summary title="Katalógus">
              <Icon name="book" />
              <span>Katalógus</span>
            </summary>
            <div className="sidebar-group-links">
              {catalogNavigation.map((item) => (
                <NavigationLink item={item} key={item.to} onNavigate={onNavigate} />
              ))}
            </div>
          </details>

          <details className="sidebar-group" open={!collapsed && procurementIsActive}>
            <summary title="Beszerzés">
              <Icon name="shopping" />
              <span>Beszerzés</span>
            </summary>
            <div className="sidebar-group-links">
              {procurementNavigation.map((item) => (
                <NavigationLink item={item} key={item.to} onNavigate={onNavigate} />
              ))}
            </div>
          </details>

          {supportNavigation.map((item) => (
            <NavigationLink item={item} key={item.to} onNavigate={onNavigate} />
          ))}
        </nav>
      </div>
    </aside>
  );
}
