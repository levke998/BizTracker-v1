import { Outlet } from "react-router-dom";
import { useState } from "react";

import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { TopbarControlsProvider } from "./TopbarControlsContext";

export function AppLayout() {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  return (
    <TopbarControlsProvider>
      <div
        className={
          isSidebarCollapsed ? "app-shell app-shell-sidebar-collapsed" : "app-shell"
        }
      >
        <Sidebar
          collapsed={isSidebarCollapsed}
          onToggleCollapsed={() => setIsSidebarCollapsed((current) => !current)}
          onNavigate={() => setIsSidebarCollapsed(true)}
        />
        <div className="app-main">
          <Topbar />
          <main className="app-content">
            <Outlet />
          </main>
        </div>
      </div>
    </TopbarControlsProvider>
  );
}
