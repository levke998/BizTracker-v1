import { useQuery } from "@tanstack/react-query";

import { listEvents } from "../api/eventsApi";

export function useEvents(
  businessUnitId: string,
  status: string,
  periodRange?: { starts_from?: string; starts_to?: string },
) {
  return useQuery({
    queryKey: ["events", businessUnitId, status, periodRange?.starts_from, periodRange?.starts_to],
    queryFn: () =>
      listEvents({
        business_unit_id: businessUnitId,
        status: status === "all" ? undefined : status,
        starts_from: periodRange?.starts_from,
        starts_to: periodRange?.starts_to,
        limit: 100,
      }),
    enabled: Boolean(businessUnitId),
  });
}
