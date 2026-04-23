import { Navigate, Route, Routes } from "react-router-dom";

import { DashboardPage } from "../modules/analytics/pages/DashboardPage";
import { TransactionsPage } from "../modules/finance/pages/TransactionsPage";
import { ImportCenterPage } from "../modules/imports/pages/ImportCenterPage";
import { InventoryOverviewPage } from "../modules/inventory/pages/InventoryOverviewPage";
import { InventoryListPage } from "../modules/inventory/pages/InventoryListPage";
import { InventoryMovementsPage } from "../modules/inventory/pages/InventoryMovementsPage";
import { StockLevelsPage } from "../modules/inventory/pages/StockLevelsPage";
import { TheoreticalStockPage } from "../modules/inventory/pages/TheoreticalStockPage";
import { MasterDataViewerPage } from "../modules/masterData/pages/MasterDataViewerPage";
import { InvoicesPage } from "../modules/procurement/pages/InvoicesPage";
import { SuppliersPage } from "../modules/procurement/pages/SuppliersPage";
import { AppLayout } from "../shared/components/layout/AppLayout";
import { routes } from "../shared/constants/routes";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Navigate replace to={routes.dashboard} />} />
        <Route path={routes.dashboard.slice(1)} element={<DashboardPage />} />
        <Route path={routes.finance.slice(1)} element={<TransactionsPage />} />
        <Route path={routes.inventory.slice(1)} element={<InventoryOverviewPage />} />
        <Route path={routes.inventoryItems.slice(1)} element={<InventoryListPage />} />
        <Route
          path={routes.inventoryMovements.slice(1)}
          element={<InventoryMovementsPage />}
        />
        <Route
          path={routes.inventoryStockLevels.slice(1)}
          element={<StockLevelsPage />}
        />
        <Route
          path={routes.inventoryTheoreticalStock.slice(1)}
          element={<TheoreticalStockPage />}
        />
        <Route
          path={routes.procurementSuppliers.slice(1)}
          element={<SuppliersPage />}
        />
        <Route
          path={routes.procurementInvoices.slice(1)}
          element={<InvoicesPage />}
        />
        <Route path={routes.masterData.slice(1)} element={<MasterDataViewerPage />} />
        <Route path={routes.imports.slice(1)} element={<ImportCenterPage />} />
      </Route>
    </Routes>
  );
}
