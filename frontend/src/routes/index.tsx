import { Navigate, Route, Routes } from "react-router-dom";

import { DashboardPage } from "../modules/analytics/pages/DashboardPage";
import { CatalogIngredientsPage } from "../modules/catalog/pages/CatalogIngredientsPage";
import { CatalogProductsPage } from "../modules/catalog/pages/CatalogProductsPage";
import { DemoPosPage } from "../modules/demoPos/pages/DemoPosPage";
import { EventsPage } from "../modules/events/pages/EventsPage";
import { TransactionsPage } from "../modules/finance/pages/TransactionsPage";
import { ImportCenterPage } from "../modules/imports/pages/ImportCenterPage";
import { LoginPage } from "../modules/identity/pages/LoginPage";
import { MasterDataViewerPage } from "../modules/masterData/pages/MasterDataViewerPage";
import { InvoicesPage } from "../modules/procurement/pages/InvoicesPage";
import { SuppliersPage } from "../modules/procurement/pages/SuppliersPage";
import { RecipesPage } from "../modules/production/pages/RecipesPage";
import { AppLayout } from "../shared/components/layout/AppLayout";
import { routes } from "../shared/constants/routes";
import { ProtectedRoute } from "./protected";

export function AppRoutes() {
  return (
    <Routes>
      <Route path={routes.login.slice(1)} element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate replace to={routes.dashboard} />} />
        <Route path={routes.dashboard.slice(1)} element={<DashboardPage />} />
        <Route path={routes.demoPos.slice(1)} element={<DemoPosPage />} />
        <Route
          path={routes.events.slice(1)}
          element={<Navigate replace to={routes.eventsNew} />}
        />
        <Route path={routes.eventsNew.slice(1)} element={<EventsPage mode="planner" />} />
        <Route
          path={routes.eventsAnalytics.slice(1)}
          element={<EventsPage mode="analytics" />}
        />
        <Route path={routes.catalogProducts.slice(1)} element={<CatalogProductsPage />} />
        <Route
          path={routes.catalogIngredients.slice(1)}
          element={<CatalogIngredientsPage />}
        />
        <Route path={routes.productionRecipes.slice(1)} element={<RecipesPage />} />
        <Route path={routes.finance.slice(1)} element={<TransactionsPage />} />
        <Route
          path={routes.inventory.slice(1)}
          element={<Navigate replace to={routes.catalogIngredients} />}
        />
        <Route
          path={routes.inventoryItems.slice(1)}
          element={<Navigate replace to={routes.catalogIngredients} />}
        />
        <Route
          path={routes.inventoryMovements.slice(1)}
          element={<Navigate replace to={routes.catalogIngredients} />}
        />
        <Route
          path={routes.inventoryStockLevels.slice(1)}
          element={<Navigate replace to={routes.catalogIngredients} />}
        />
        <Route
          path={routes.inventoryTheoreticalStock.slice(1)}
          element={<Navigate replace to={routes.catalogIngredients} />}
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
