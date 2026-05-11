import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "../shared/components/layout/AppLayout";
import { routes } from "../shared/constants/routes";
import { ProtectedRoute } from "./protected";

const CatalogIngredientsPage = lazy(() =>
  import("../modules/catalog/pages/CatalogIngredientsPage").then((module) => ({
    default: module.CatalogIngredientsPage,
  })),
);
const CatalogProductsPage = lazy(() =>
  import("../modules/catalog/pages/CatalogProductsPage").then((module) => ({
    default: module.CatalogProductsPage,
  })),
);
const DashboardPage = lazy(() =>
  import("../modules/analytics/pages/DashboardPage").then((module) => ({
    default: module.DashboardPage,
  })),
);
const DemoPosPage = lazy(() =>
  import("../modules/demoPos/pages/DemoPosPage").then((module) => ({
    default: module.DemoPosPage,
  })),
);
const EventsPage = lazy(() =>
  import("../modules/events/pages/EventsPage").then((module) => ({
    default: module.EventsPage,
  })),
);
const ImportCenterPage = lazy(() =>
  import("../modules/imports/pages/ImportCenterPage").then((module) => ({
    default: module.ImportCenterPage,
  })),
);
const InvoicesPage = lazy(() =>
  import("../modules/procurement/pages/InvoicesPage").then((module) => ({
    default: module.InvoicesPage,
  })),
);
const LoginPage = lazy(() =>
  import("../modules/identity/pages/LoginPage").then((module) => ({
    default: module.LoginPage,
  })),
);
const MasterDataViewerPage = lazy(() =>
  import("../modules/masterData/pages/MasterDataViewerPage").then((module) => ({
    default: module.MasterDataViewerPage,
  })),
);
const RecipesPage = lazy(() =>
  import("../modules/production/pages/RecipesPage").then((module) => ({
    default: module.RecipesPage,
  })),
);
const SuppliersPage = lazy(() =>
  import("../modules/procurement/pages/SuppliersPage").then((module) => ({
    default: module.SuppliersPage,
  })),
);
const TransactionsPage = lazy(() =>
  import("../modules/finance/pages/TransactionsPage").then((module) => ({
    default: module.TransactionsPage,
  })),
);

function RouteFallback() {
  return <p className="info-message">Oldal betöltése...</p>;
}

export function AppRoutes() {
  return (
    <Suspense fallback={<RouteFallback />}>
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
    </Suspense>
  );
}
