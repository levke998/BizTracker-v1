import { Navigate, Route, Routes } from "react-router-dom";

import { TransactionsPage } from "../modules/finance/pages/TransactionsPage";
import { ImportCenterPage } from "../modules/imports/pages/ImportCenterPage";
import { InventoryListPage } from "../modules/inventory/pages/InventoryListPage";
import { MasterDataViewerPage } from "../modules/masterData/pages/MasterDataViewerPage";
import { AppLayout } from "../shared/components/layout/AppLayout";
import { routes } from "../shared/constants/routes";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Navigate replace to={routes.masterData} />} />
        <Route path={routes.finance.slice(1)} element={<TransactionsPage />} />
        <Route path={routes.inventory.slice(1)} element={<InventoryListPage />} />
        <Route path={routes.masterData.slice(1)} element={<MasterDataViewerPage />} />
        <Route path={routes.imports.slice(1)} element={<ImportCenterPage />} />
      </Route>
    </Routes>
  );
}
