import { useSyncExternalStore, type PropsWithChildren } from "react";
import { Navigate, useLocation } from "react-router-dom";

import {
  getAccessToken,
  subscribeToAuthChanges,
} from "../services/storage/tokenStorage";
import { routes } from "../shared/constants/routes";

export function ProtectedRoute({ children }: PropsWithChildren) {
  const location = useLocation();
  const token = useSyncExternalStore(
    subscribeToAuthChanges,
    getAccessToken,
    getAccessToken,
  );

  if (!token) {
    return <Navigate replace to={routes.login} state={{ from: location }} />;
  }

  return children;
}
