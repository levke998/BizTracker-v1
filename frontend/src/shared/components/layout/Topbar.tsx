import { useLocation } from "react-router-dom";

import { routes } from "../../constants/routes";

function getPageMeta(pathname: string) {
  if (pathname.startsWith(routes.dashboard)) {
    return {
      title: "Business Dashboard",
      subtitle:
        "Overall, Flow and Gourmand business performance with KPI tiles, trends, costs and drill-down ready breakdowns.",
    };
  }

  if (pathname.startsWith(routes.demoPos)) {
    return {
      title: "Demo POS",
      subtitle:
        "Standalone test register that sends receipt lines into the import, finance and dashboard pipeline.",
    };
  }

  if (pathname.startsWith(routes.catalogProducts)) {
    return {
      title: "Catalog Products",
      subtitle:
        "Sellable product catalog with price, estimated cost, margin and recipe visibility.",
    };
  }

  if (pathname.startsWith(routes.catalogIngredients)) {
    return {
      title: "Catalog Ingredients",
      subtitle:
        "Ingredient and material catalog with latest known costs, estimated stock and recipe usage.",
    };
  }

  if (pathname.startsWith(routes.finance)) {
    return {
      title: "Finance Transactions",
      subtitle:
        "Transaction lists and filters using the same dark surface, hierarchy and table styling.",
    };
  }

  if (pathname.startsWith(routes.inventoryStockLevels)) {
    return {
      title: "Stock Levels",
      subtitle:
        "Operational inventory data with calmer table surfaces and more polished filter states.",
    };
  }

  if (pathname.startsWith(routes.inventoryTheoreticalStock)) {
    return {
      title: "Theoretical Stock",
      subtitle:
        "Variance and reconciliation views aligned to the same panel, input and feedback language.",
    };
  }

  if (pathname.startsWith(routes.inventoryMovements)) {
    return {
      title: "Inventory Movements",
      subtitle:
        "Readable movement tracking with subtle separators and consistent dark controls.",
    };
  }

  if (pathname.startsWith(routes.inventoryItems)) {
    return {
      title: "Inventory Items",
      subtitle:
        "Master item maintenance presented with rounded surfaces, focus glow and improved spacing.",
    };
  }

  if (pathname.startsWith(routes.inventory)) {
    return {
      title: "Inventory Overview",
      subtitle:
        "Overview panels, KPIs and tables styled to feel modern without changing the functional flow.",
    };
  }

  if (pathname.startsWith(routes.procurementSuppliers)) {
    return {
      title: "Suppliers",
      subtitle:
        "Procurement partner registry with the same panel, filter and maintenance patterns used across the platform.",
    };
  }

  if (pathname.startsWith(routes.procurementInvoices)) {
    return {
      title: "Purchase Invoices",
      subtitle:
        "Manual procurement invoice capture prepared for later PDF ingestion, inventory growth and cost-side workflows.",
    };
  }

  if (pathname.startsWith(routes.imports)) {
    return {
      title: "Import Center",
      subtitle:
        "Workflow-focused dark UI for uploads, statuses and parsing details with softer emphasis.",
    };
  }

  return {
    title: "Master Data Viewer",
    subtitle:
      "Core master data screens using the same visual system so the app feels cohesive as it grows.",
  };
}

export function Topbar() {
  const location = useLocation();
  const pageMeta = getPageMeta(location.pathname);
  const formattedDate = new Intl.DateTimeFormat("hu-HU", {
    month: "short",
    day: "2-digit",
    year: "numeric",
  }).format(new Date());

  return (
    <header className="topbar">
      <div className="topbar-copy">
        <span className="topbar-eyebrow">BizTracker Internal Platform</span>
        <h1 className="topbar-title">{pageMeta.title}</h1>
        <p className="topbar-subtitle">{pageMeta.subtitle}</p>
      </div>
      <div className="topbar-actions">
        <span className="topbar-chip topbar-chip-primary">Business read model</span>
        <span className="topbar-chip">Readable dark enterprise UI</span>
        <span className="topbar-chip">{formattedDate}</span>
      </div>
    </header>
  );
}
