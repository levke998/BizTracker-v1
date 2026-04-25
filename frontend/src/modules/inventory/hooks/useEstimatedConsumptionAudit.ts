import { useQuery } from "@tanstack/react-query";

import { listEstimatedConsumptionAudit } from "../api/inventoryApi";
import type { EstimatedConsumptionAuditFilters } from "../types/inventory";

export function useEstimatedConsumptionAudit(filters: EstimatedConsumptionAuditFilters) {
  const hasScope = Boolean(filters.business_unit_id || filters.inventory_item_id);

  return useQuery({
    queryKey: ["inventory-estimated-consumption", filters],
    queryFn: () => listEstimatedConsumptionAudit(filters),
    enabled: hasScope,
  });
}
