import { useLocation } from "react-router-dom";

import { routes } from "../../constants/routes";

function getTitle(pathname: string) {
  if (pathname.startsWith(routes.imports)) {
    return "Import Center";
  }

  return "Master Data Viewer";
}

export function Topbar() {
  const location = useLocation();

  return (
    <header className="topbar">
      <div>
        <h1 className="topbar-title">{getTitle(location.pathname)}</h1>
        <p className="topbar-subtitle">Minimal internal frontend integration</p>
      </div>
    </header>
  );
}
