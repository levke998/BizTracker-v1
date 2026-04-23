import { NavLink } from "react-router-dom";

import { routes } from "../../constants/routes";

const navigation = [
  { to: routes.masterData, label: "Master Data Viewer" },
  { to: routes.imports, label: "Import Center" },
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="sidebar-brand-title">BizTracker</span>
        <span className="sidebar-brand-subtitle">Internal tools</span>
      </div>

      <nav className="sidebar-nav">
        {navigation.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              isActive ? "sidebar-link sidebar-link-active" : "sidebar-link"
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
