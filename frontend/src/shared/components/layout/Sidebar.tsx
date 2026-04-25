import { NavLink } from "react-router-dom";

import { routes } from "../../constants/routes";

const navigation = [
  { to: routes.dashboard, label: "Dashboard" },
  { to: routes.demoPos, label: "Demo POS" },
  { to: routes.catalogProducts, label: "Catalog - Products" },
  { to: routes.catalogIngredients, label: "Catalog - Ingredients" },
  { to: routes.masterData, label: "Master Data Viewer" },
  { to: routes.finance, label: "Finance Transactions" },
  { to: routes.inventory, label: "Inventory Overview" },
  { to: routes.inventoryItems, label: "Inventory Items" },
  { to: routes.inventoryMovements, label: "Inventory Movements" },
  { to: routes.inventoryStockLevels, label: "Stock Levels" },
  { to: routes.inventoryTheoreticalStock, label: "Theoretical Stock" },
  { to: routes.procurementSuppliers, label: "Suppliers" },
  { to: routes.procurementInvoices, label: "Purchase Invoices" },
  { to: routes.imports, label: "Import Center" },
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="sidebar-brand-title">BizTracker</span>
        <span className="sidebar-brand-subtitle">Internal operations workspace</span>
      </div>

      <div className="sidebar-section">
        <span className="sidebar-section-label">Navigation</span>
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
      </div>

      <div className="sidebar-footer">
        <span className="sidebar-footer-label">Theme direction</span>
        <strong>Dark premium foundation</strong>
        <span>Soft purple glow, readable enterprise surfaces, stronger chart accents.</span>
      </div>
    </aside>
  );
}
