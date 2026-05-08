import { apiDelete, apiGet, apiPost, apiPostJson, apiPutJson } from "../../../services/api/client";
import type {
  EventFilters,
  EventPayload,
  EventPerformance,
  EventRecord,
  EventTicketActual,
  EventTicketActualPayload,
  EventWeatherCoverage,
} from "../types/events";

export function listEvents(filters: EventFilters) {
  return apiGet<EventRecord[]>("events", filters);
}

export function listEventPerformances(filters: EventFilters) {
  return apiGet<EventPerformance[]>("events/performance", filters);
}

export function createEvent(payload: EventPayload) {
  return apiPostJson<EventPayload, EventRecord>("events", payload);
}

export function updateEvent(eventId: string, payload: EventPayload) {
  return apiPutJson<EventPayload, EventRecord>(`events/${eventId}`, payload);
}

export function archiveEvent(eventId: string) {
  return apiDelete<EventRecord>(`events/${eventId}`);
}

export function getEventPerformance(eventId: string) {
  return apiGet<EventPerformance>(`events/${eventId}/performance`);
}

export function getEventTicketActual(eventId: string) {
  return apiGet<EventTicketActual | null>(`events/${eventId}/ticket-actual`);
}

export function upsertEventTicketActual(eventId: string, payload: EventTicketActualPayload) {
  return apiPutJson<EventTicketActualPayload, EventTicketActual>(
    `events/${eventId}/ticket-actual`,
    payload,
  );
}

export function ensureEventWeatherCoverage(eventId: string) {
  return apiPost<EventWeatherCoverage>(`events/${eventId}/weather/ensure-coverage`);
}
