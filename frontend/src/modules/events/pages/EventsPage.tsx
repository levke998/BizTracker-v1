import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useTopbarControls } from "../../../shared/components/layout/TopbarControlsContext";
import { Button } from "../../../shared/components/ui/Button";
import { Card } from "../../../shared/components/ui/Card";
import { listBusinessUnits, listLocations, listVatRates } from "../../masterData/api/masterDataApi";
import {
  archiveEvent,
  createEvent,
  ensureEventWeatherCoverage,
  getEventPerformance,
  getEventTicketActual,
  listEventPerformances,
  upsertEventTicketActual,
  updateEvent,
} from "../api/eventsApi";
import { useEvents } from "../hooks/useEvents";
import type {
  EventPayload,
  EventPerformance,
  EventRecord,
  EventStatus,
  EventTicketActualPayload,
  EventWeatherCoverage,
} from "../types/events";

type EventFormState = {
  id?: string;
  location_id: string;
  title: string;
  status: EventStatus;
  starts_at: string;
  ends_at: string;
  performer_name: string;
  expected_attendance: string;
  ticket_revenue_gross: string;
  bar_revenue_gross: string;
  performer_share_percent: string;
  performer_fixed_fee: string;
  event_cost_amount: string;
  notes: string;
  is_active: boolean;
};
type TicketActualFormState = {
  source_name: string;
  source_reference: string;
  sold_quantity: string;
  gross_revenue: string;
  net_revenue: string;
  vat_amount: string;
  vat_rate_id: string;
  platform_fee_gross: string;
  reported_at: string;
  notes: string;
};
type EventPeriod = "alltime" | "last_30_days" | "last_90_days" | "year";
type EventsPageMode = "planner" | "analytics";
type CalendarDay = {
  key: string;
  dayNumber: number;
  isCurrentMonth: boolean;
  isToday: boolean;
  events: EventRecord[];
};

const statusOptions: Array<{ value: EventStatus | "all"; label: string }> = [
  { value: "all", label: "Minden státusz" },
  { value: "planned", label: "Tervezett" },
  { value: "confirmed", label: "Visszaigazolt" },
  { value: "completed", label: "Lezárt" },
  { value: "cancelled", label: "Lemondott" },
];
const periodOptions: Array<{ value: EventPeriod; label: string }> = [
  { value: "alltime", label: "All-time" },
  { value: "last_30_days", label: "Elmúlt 30 nap" },
  { value: "last_90_days", label: "Elmúlt 90 nap" },
  { value: "year", label: "Aktuális év" },
];

function toNumber(value: string | number | null | undefined) {
  const parsed = Number(value ?? 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatMoney(value: string | number | null | undefined) {
  return new Intl.NumberFormat("hu-HU", {
    style: "currency",
    currency: "HUF",
    maximumFractionDigits: 0,
  }).format(toNumber(value));
}

function formatNumber(value: string | number | null | undefined) {
  return new Intl.NumberFormat("hu-HU", {
    maximumFractionDigits: 1,
  }).format(toNumber(value));
}

function formatPercent(value: number) {
  return new Intl.NumberFormat("hu-HU", {
    maximumFractionDigits: 1,
  }).format(value);
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat("hu-HU", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatShortTime(value: string | null) {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat("hu-HU", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatMonthLabel(value: Date) {
  return new Intl.DateTimeFormat("hu-HU", {
    year: "numeric",
    month: "long",
  }).format(value);
}

function formatStatus(value: string) {
  return statusOptions.find((option) => option.value === value)?.label ?? value;
}

function formatWeatherCondition(value: string | null) {
  const labels: Record<string, string> = {
    napos: "Napos",
    napos_szaraz: "Napos / száraz",
    reszben_felhos: "Részben felhős",
    borult: "Borult",
    kodos: "Ködös",
    esos: "Esős",
    havas: "Havas",
    szeles: "Szeles",
    viharos: "Viharos",
    ismeretlen: "Ismeretlen",
  };
  return value ? labels[value] ?? value : "-";
}

function formatEventWeatherSummary(performance: EventPerformance) {
  if (performance.weather.observation_count === 0) {
    return "Nincs cache-elt időjárás az event időablakára";
  }

  const temperature = performance.weather.average_temperature_c
    ? `${formatNumber(performance.weather.average_temperature_c)} °C`
    : "-";
  return `${formatWeatherCondition(performance.weather.dominant_condition)} · ${temperature}`;
}

function getTicketSharePercent(performance: EventPerformance) {
  const total = toNumber(performance.total_revenue_gross);
  if (total <= 0) {
    return 0;
  }
  return (toNumber(performance.ticket_revenue_gross) / total) * 100;
}

function getWeatherImpactLabel(performance: EventPerformance) {
  if (performance.weather.observation_count === 0) {
    return "Időjárás nélkül";
  }
  const precipitation = toNumber(performance.weather.total_precipitation_mm);
  const temperature = toNumber(performance.weather.average_temperature_c);
  const condition = performance.weather.dominant_condition;

  if (precipitation > 0 || condition === "esos" || condition === "viharos") {
    return "Csapadékos event";
  }
  if (temperature >= 28) {
    return "Meleg/nyári hatás";
  }
  if (temperature <= 8 && temperature !== 0) {
    return "Hideg idő";
  }
  return formatWeatherCondition(condition);
}

function formatWeatherCoverageLabel(
  performance: EventPerformance | null,
  coverage: EventWeatherCoverage | undefined,
) {
  if (coverage?.status === "backfilled") {
    return coverage.created_count > 0
      ? `${coverage.created_count} új óra előkészítve`
      : "Időjárás cache frissítve";
  }
  if (coverage?.status === "covered") {
    return "Időjárás cache rendben";
  }
  if (coverage?.status === "skipped") {
    return "Előkészítés nem indult";
  }
  if (performance && performance.weather.observation_count > 0) {
    return "Időjárás cache rendben";
  }
  return "Időjárás cache hiányos";
}

function formatWeatherCoverageHelp(
  performance: EventPerformance | null,
  coverage: EventWeatherCoverage | undefined,
) {
  if (coverage?.reason) {
    return coverage.reason;
  }
  if (coverage) {
    return `${coverage.cached_hours}/${coverage.requested_hours} óra cache-elve, ${coverage.missing_hours} hiányzik.`;
  }
  if (performance && performance.weather.observation_count > 0) {
    return `${performance.weather.observation_count} órás Szolnok megfigyelés kapcsolódik ehhez az eventhez.`;
  }
  return "Az event idősávjára még nincs cache-elt Szolnok időjárás. Múltbeli eventnél előkészíthető.";
}

function toDateTimeInput(value: string | null) {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  const offsetDate = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return offsetDate.toISOString().slice(0, 16);
}

function buildForm(event?: EventRecord): EventFormState {
  return {
    id: event?.id,
    location_id: event?.location_id ?? "",
    title: event?.title ?? "",
    status: event?.status ?? "planned",
    starts_at: event ? toDateTimeInput(event.starts_at) : "",
    ends_at: event ? toDateTimeInput(event.ends_at) : "",
    performer_name: event?.performer_name ?? "",
    expected_attendance: event?.expected_attendance?.toString() ?? "",
    ticket_revenue_gross: event?.ticket_revenue_gross ?? "0",
    bar_revenue_gross: event?.bar_revenue_gross ?? "0",
    performer_share_percent: event?.performer_share_percent ?? "80",
    performer_fixed_fee: event?.performer_fixed_fee ?? "0",
    event_cost_amount: event?.event_cost_amount ?? "0",
    notes: event?.notes ?? "",
    is_active: event?.is_active ?? true,
  };
}

function buildTicketActualForm(): TicketActualFormState {
  return {
    source_name: "",
    source_reference: "",
    sold_quantity: "",
    gross_revenue: "",
    net_revenue: "",
    vat_amount: "",
    vat_rate_id: "",
    platform_fee_gross: "",
    reported_at: "",
    notes: "",
  };
}

function compactNullable(value: string) {
  return value.trim() === "" ? null : value.trim();
}

function toIsoDateTime(value: string) {
  return new Date(value).toISOString();
}

function optionalIsoDateTime(value: string) {
  return value ? new Date(value).toISOString() : null;
}

function getEventPeriodRange(period: EventPeriod) {
  if (period === "alltime") {
    return {};
  }

  const now = new Date();
  if (period === "year") {
    return {
      starts_from: new Date(now.getFullYear(), 0, 1).toISOString(),
      starts_to: now.toISOString(),
    };
  }

  const days = period === "last_30_days" ? 30 : 90;
  const start = new Date(now);
  start.setDate(now.getDate() - days);
  return {
    starts_from: start.toISOString(),
    starts_to: now.toISOString(),
  };
}

function getLocalDateKey(value: Date) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getCalendarAnchor(events: EventRecord[]) {
  const now = new Date();
  const upcoming = events
    .filter((event) => new Date(event.starts_at).getTime() >= now.getTime())
    .sort((left, right) => new Date(left.starts_at).getTime() - new Date(right.starts_at).getTime())[0];

  if (upcoming) {
    return new Date(upcoming.starts_at);
  }

  const latest = [...events].sort(
    (left, right) => new Date(right.starts_at).getTime() - new Date(left.starts_at).getTime(),
  )[0];
  return latest ? new Date(latest.starts_at) : now;
}

function buildCalendarDays(events: EventRecord[], anchor: Date): CalendarDay[] {
  const monthStart = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
  const calendarStart = new Date(monthStart);
  const mondayBasedOffset = (monthStart.getDay() + 6) % 7;
  calendarStart.setDate(monthStart.getDate() - mondayBasedOffset);

  const eventsByDay = events.reduce((map, event) => {
    const key = getLocalDateKey(new Date(event.starts_at));
    const dayEvents = map.get(key) ?? [];
    dayEvents.push(event);
    map.set(key, dayEvents);
    return map;
  }, new Map<string, EventRecord[]>());

  const todayKey = getLocalDateKey(new Date());
  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(calendarStart);
    date.setDate(calendarStart.getDate() + index);
    const key = getLocalDateKey(date);
    return {
      key,
      dayNumber: date.getDate(),
      isCurrentMonth: date.getMonth() === anchor.getMonth(),
      isToday: key === todayKey,
      events: (eventsByDay.get(key) ?? []).sort(
        (left, right) => new Date(left.starts_at).getTime() - new Date(right.starts_at).getTime(),
      ),
    };
  });
}

function EventsHeaderControls({
  businessUnits,
  selectedBusinessUnitId,
  setSelectedBusinessUnitId,
  status,
  setStatus,
  period,
  setPeriod,
  startCreate,
  mode,
}: {
  businessUnits: Array<{ id: string; name: string }>;
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  status: string;
  setStatus: (value: string) => void;
  period: EventPeriod;
  setPeriod: (value: EventPeriod) => void;
  startCreate: () => void;
  mode: EventsPageMode;
}) {
  return (
    <div className="business-dashboard-filters topbar-dashboard-filters">
      <label className="field topbar-field">
        <span>Vállalkozás</span>
        <select
          className="field-input"
          value={selectedBusinessUnitId}
          onChange={(event) => setSelectedBusinessUnitId(event.target.value)}
        >
          {businessUnits.map((businessUnit) => (
            <option key={businessUnit.id} value={businessUnit.id}>
              {businessUnit.name}
            </option>
          ))}
        </select>
      </label>
      <label className="field topbar-field">
        <span>Státusz</span>
        <select
          className="field-input"
          value={status}
          onChange={(event) => setStatus(event.target.value)}
        >
          {statusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
      <label className="field topbar-field">
        <span>Időszak</span>
        <select
          className="field-input"
          value={period}
          onChange={(event) => setPeriod(event.target.value as EventPeriod)}
        >
          {periodOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
      {mode === "planner" ? (
        <Button type="button" onClick={startCreate}>
          Új esemény
        </Button>
      ) : null}
    </div>
  );
}

export function EventsPage({ mode = "planner" }: { mode?: EventsPageMode }) {
  const { setControls } = useTopbarControls();
  const queryClient = useQueryClient();
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [selectedPeriod, setSelectedPeriod] = useState<EventPeriod>("alltime");
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(mode === "planner");
  const [form, setForm] = useState<EventFormState>(() => buildForm());
  const [ticketActualForm, setTicketActualForm] = useState<TicketActualFormState>(() =>
    buildTicketActualForm(),
  );
  const [weatherCoverageByEventId, setWeatherCoverageByEventId] = useState<
    Record<string, EventWeatherCoverage | undefined>
  >({});

  const businessUnitsQuery = useQuery({
    queryKey: ["business-units"],
    queryFn: listBusinessUnits,
  });
  const businessUnits = businessUnitsQuery.data ?? [];
  const flowBusinessUnit = businessUnits.find((businessUnit) => businessUnit.code === "flow");

  useEffect(() => {
    if (!selectedBusinessUnitId && businessUnits.length > 0) {
      setSelectedBusinessUnitId(flowBusinessUnit?.id ?? businessUnits[0].id);
    }
  }, [businessUnits, flowBusinessUnit?.id, selectedBusinessUnitId]);

  const locationsQuery = useQuery({
    queryKey: ["locations", selectedBusinessUnitId],
    queryFn: () => listLocations(selectedBusinessUnitId),
    enabled: Boolean(selectedBusinessUnitId),
  });
  const vatRatesQuery = useQuery({
    queryKey: ["vat-rates"],
    queryFn: listVatRates,
  });
  const eventPeriodRange = useMemo(
    () => getEventPeriodRange(selectedPeriod),
    [selectedPeriod],
  );
  const eventsQuery = useEvents(selectedBusinessUnitId, selectedStatus, eventPeriodRange);
  const eventPerformancesQuery = useQuery({
    queryKey: [
      "event-performances",
      selectedBusinessUnitId,
      selectedStatus,
      eventPeriodRange.starts_from,
      eventPeriodRange.starts_to,
    ],
    queryFn: () =>
      listEventPerformances({
        business_unit_id: selectedBusinessUnitId,
        status: selectedStatus === "all" ? undefined : selectedStatus,
        ...eventPeriodRange,
        limit: 200,
      }),
    enabled: Boolean(selectedBusinessUnitId) && mode === "analytics",
  });
  const eventPerformanceQuery = useQuery({
    queryKey: ["event-performance", expandedEventId],
    queryFn: () => getEventPerformance(expandedEventId as string),
    enabled: Boolean(expandedEventId),
  });
  const ticketActualQuery = useQuery({
    queryKey: ["event-ticket-actual", expandedEventId],
    queryFn: () => getEventTicketActual(expandedEventId as string),
    enabled: Boolean(expandedEventId),
  });
  const events = eventsQuery.data ?? [];
  const eventPerformances = eventPerformancesQuery.data ?? [];
  const locations = locationsQuery.data ?? [];
  const vatRates = vatRatesQuery.data ?? [];
  const isPlanner = mode === "planner";
  const eventById = useMemo(
    () => new Map(events.map((event) => [event.id, event])),
    [events],
  );
  const performanceByEventId = useMemo(
    () => new Map(eventPerformances.map((performance) => [performance.event_id, performance])),
    [eventPerformances],
  );

  const saveMutation = useMutation({
    mutationFn: (payload: EventPayload & { id?: string }) => {
      if (payload.id) {
        const { id, ...body } = payload;
        return updateEvent(id, body);
      }
      return createEvent(payload);
    },
    onSuccess: (event) => {
      setIsCreating(false);
      setExpandedEventId(event.id);
      setForm(buildForm(event));
      void queryClient.invalidateQueries({ queryKey: ["events"] });
    },
  });

  const archiveMutation = useMutation({
    mutationFn: archiveEvent,
    onSuccess: () => {
      setExpandedEventId(null);
      setIsCreating(false);
      setForm(buildForm());
      void queryClient.invalidateQueries({ queryKey: ["events"] });
    },
  });

  const weatherCoverageMutation = useMutation({
    mutationFn: ensureEventWeatherCoverage,
    onSuccess: (coverage, eventId) => {
      setWeatherCoverageByEventId((current) => ({
        ...current,
        [eventId]: coverage,
      }));
      void queryClient.invalidateQueries({ queryKey: ["event-performance", eventId] });
      void queryClient.invalidateQueries({ queryKey: ["event-performances"] });
    },
  });
  const ticketActualMutation = useMutation({
    mutationFn: ({
      eventId,
      payload,
    }: {
      eventId: string;
      payload: EventTicketActualPayload;
    }) => upsertEventTicketActual(eventId, payload),
    onSuccess: (actual) => {
      void queryClient.invalidateQueries({ queryKey: ["event-ticket-actual", actual.event_id] });
      void queryClient.invalidateQueries({ queryKey: ["event-performance", actual.event_id] });
      void queryClient.invalidateQueries({ queryKey: ["event-performances"] });
    },
  });

  useEffect(() => {
    const actual = ticketActualQuery.data;
    if (!expandedEventId) {
      setTicketActualForm(buildTicketActualForm());
      return;
    }
    if (!actual) {
      setTicketActualForm(buildTicketActualForm());
      return;
    }
    setTicketActualForm({
      source_name: actual.source_name ?? "",
      source_reference: actual.source_reference ?? "",
      sold_quantity: actual.sold_quantity,
      gross_revenue: actual.gross_revenue,
      net_revenue: actual.net_revenue ?? "",
      vat_amount: actual.vat_amount ?? "",
      vat_rate_id: actual.vat_rate_id ?? "",
      platform_fee_gross: actual.platform_fee_gross,
      reported_at: actual.reported_at ? toDateTimeInput(actual.reported_at) : "",
      notes: actual.notes ?? "",
    });
  }, [expandedEventId, ticketActualQuery.data]);

  const summary = useMemo(() => {
    const sourceRows = isPlanner ? events : eventPerformances;
    return sourceRows.reduce(
      (acc, item) => ({
        ticketRevenue: acc.ticketRevenue + toNumber(item.ticket_revenue_gross),
        barRevenue: acc.barRevenue + toNumber(item.bar_revenue_gross),
        ownRevenue: acc.ownRevenue + toNumber(item.own_revenue),
        profit: acc.profit + toNumber(item.event_profit_lite),
        receiptCount:
          acc.receiptCount + ("receipt_count" in item ? Number(item.receipt_count) : 0),
      }),
      { ticketRevenue: 0, barRevenue: 0, ownRevenue: 0, profit: 0, receiptCount: 0 },
    );
  }, [eventPerformances, events, isPlanner]);
  const performerRows = useMemo(() => {
    return Array.from(
      (isPlanner ? events : eventPerformances)
        .reduce(
          (map, item) => {
            const event = "event_id" in item ? eventById.get(item.event_id) : item;
            if (event?.status === "cancelled") {
              return map;
            }
            const performer = event?.performer_name ?? "Fellépő nélkül";
            const current = map.get(performer) ?? {
              performer,
              eventCount: 0,
              ticketRevenue: 0,
              barRevenue: 0,
              ownRevenue: 0,
              profit: 0,
            };
            current.eventCount += 1;
            current.ticketRevenue += toNumber(item.ticket_revenue_gross);
            current.barRevenue += toNumber(item.bar_revenue_gross);
            current.ownRevenue += toNumber(item.own_revenue);
            current.profit += toNumber(item.event_profit_lite);
            map.set(performer, current);
            return map;
          },
          new Map<
            string,
            {
              performer: string;
              eventCount: number;
              ticketRevenue: number;
              barRevenue: number;
              ownRevenue: number;
              profit: number;
            }
          >(),
        )
        .values(),
    ).sort((left, right) => right.profit - left.profit);
  }, [eventById, eventPerformances, events, isPlanner]);
  const topPerformance = useMemo(
    () =>
      [...eventPerformances].sort(
        (left, right) => toNumber(right.event_profit_lite) - toNumber(left.event_profit_lite),
      )[0],
    [eventPerformances],
  );
  const mostPopularPerformance = useMemo(
    () =>
      [...eventPerformances].sort((left, right) => {
        const receiptDiff = Number(right.receipt_count) - Number(left.receipt_count);
        if (receiptDiff !== 0) {
          return receiptDiff;
        }
        return Number(right.source_row_count) - Number(left.source_row_count);
      })[0],
    [eventPerformances],
  );
  const highestRevenuePerformance = useMemo(
    () =>
      [...eventPerformances].sort(
        (left, right) => toNumber(right.total_revenue_gross) - toNumber(left.total_revenue_gross),
      )[0],
    [eventPerformances],
  );
  const comparisonRows = useMemo(
    () =>
      [...eventPerformances]
        .sort((left, right) => toNumber(right.event_profit_lite) - toNumber(left.event_profit_lite))
        .slice(0, 10),
    [eventPerformances],
  );
  const plannedEvents = useMemo(
    () => events.filter((event) => event.status === "planned" || event.status === "confirmed"),
    [events],
  );
  const calendarAnchor = useMemo(() => getCalendarAnchor(events), [events]);
  const calendarDays = useMemo(
    () => buildCalendarDays(events, calendarAnchor),
    [calendarAnchor, events],
  );
  const nextEvent = useMemo(
    () =>
      plannedEvents
        .filter((event) => new Date(event.starts_at).getTime() >= Date.now())
        .sort((left, right) => new Date(left.starts_at).getTime() - new Date(right.starts_at).getTime())[0],
    [plannedEvents],
  );

  function startCreate() {
    setIsCreating(true);
    setExpandedEventId(null);
    setForm(buildForm());
  }

  function startEdit(event: EventRecord) {
    setIsCreating(true);
    setExpandedEventId(event.id);
    setForm(buildForm(event));
  }

  function buildPayload(): EventPayload & { id?: string } {
    return {
      id: form.id,
      business_unit_id: selectedBusinessUnitId,
      location_id: compactNullable(form.location_id),
      title: form.title.trim(),
      status: form.status,
      starts_at: toIsoDateTime(form.starts_at),
      ends_at: form.ends_at ? toIsoDateTime(form.ends_at) : null,
      performer_name: compactNullable(form.performer_name),
      expected_attendance: form.expected_attendance ? Number(form.expected_attendance) : null,
      ticket_revenue_gross: form.ticket_revenue_gross || "0",
      bar_revenue_gross: form.bar_revenue_gross || "0",
      performer_share_percent: form.performer_share_percent || "80",
      performer_fixed_fee: form.performer_fixed_fee || "0",
      event_cost_amount: form.event_cost_amount || "0",
      notes: compactNullable(form.notes),
      is_active: form.is_active,
    };
  }

  function buildTicketActualPayload(): EventTicketActualPayload {
    return {
      source_name: compactNullable(ticketActualForm.source_name),
      source_reference: compactNullable(ticketActualForm.source_reference),
      sold_quantity: ticketActualForm.sold_quantity || "0",
      gross_revenue: ticketActualForm.gross_revenue || "0",
      net_revenue: compactNullable(ticketActualForm.net_revenue),
      vat_amount: compactNullable(ticketActualForm.vat_amount),
      vat_rate_id: compactNullable(ticketActualForm.vat_rate_id),
      platform_fee_gross: ticketActualForm.platform_fee_gross || "0",
      reported_at: optionalIsoDateTime(ticketActualForm.reported_at),
      notes: compactNullable(ticketActualForm.notes),
    };
  }

  function saveTicketActual(eventId: string) {
    ticketActualMutation.mutate({
      eventId,
      payload: buildTicketActualPayload(),
    });
  }

  function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    saveMutation.mutate(buildPayload());
  }

  useEffect(() => {
    setControls(
      <EventsHeaderControls
        businessUnits={businessUnits}
        selectedBusinessUnitId={selectedBusinessUnitId}
        setSelectedBusinessUnitId={(value) => {
          setSelectedBusinessUnitId(value);
          setExpandedEventId(null);
          setIsCreating(false);
        }}
        status={selectedStatus}
        setStatus={setSelectedStatus}
        period={selectedPeriod}
        setPeriod={setSelectedPeriod}
        startCreate={startCreate}
        mode={mode}
      />,
    );
    return () => setControls(null);
  }, [businessUnits, mode, selectedBusinessUnitId, selectedPeriod, selectedStatus, setControls]);

  const formPanel = isCreating ? (
    <Card
      className="event-editor-card"
      eyebrow={form.id ? "Esemény szerkesztése" : "Új Flow esemény"}
      title={form.id ? form.title : "Esemény időablak rögzítése"}
      subtitle="A jegy- és bárbevétel nem előre megadott adat: az esemény időszakára érkező POS/API/CSV sorokból kapcsolódik majd."
    >
      <form className="event-form" onSubmit={submitForm}>
        <div className="form-grid">
          <label className="field">
            <span>Esemény neve</span>
            <input className="field-input" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} required />
          </label>
          <label className="field">
            <span>Helyszín</span>
            <select className="field-input" value={form.location_id} onChange={(event) => setForm({ ...form, location_id: event.target.value })}>
              <option value="">Nincs kiválasztva</option>
              {locations.map((location) => (
                <option key={location.id} value={location.id}>{location.name}</option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Státusz</span>
            <select className="field-input" value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value as EventStatus })}>
              {statusOptions.filter((option) => option.value !== "all").map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Kezdés</span>
            <input className="field-input" type="datetime-local" value={form.starts_at} onChange={(event) => setForm({ ...form, starts_at: event.target.value })} required />
          </label>
          <label className="field">
            <span>Zárás</span>
            <input className="field-input" type="datetime-local" value={form.ends_at} onChange={(event) => setForm({ ...form, ends_at: event.target.value })} />
          </label>
          <label className="field">
            <span>Fellépő</span>
            <input className="field-input" value={form.performer_name} onChange={(event) => setForm({ ...form, performer_name: event.target.value })} />
          </label>
          <label className="field">
            <span>Várt létszám</span>
            <input className="field-input" type="number" min="0" value={form.expected_attendance} onChange={(event) => setForm({ ...form, expected_attendance: event.target.value })} />
          </label>
          <label className="field">
            <span>Fellépő részesedés %</span>
            <input className="field-input" type="number" min="0" max="100" step="0.01" value={form.performer_share_percent} onChange={(event) => setForm({ ...form, performer_share_percent: event.target.value })} />
          </label>
          <label className="field">
            <span>Fix fellépti díj</span>
            <input className="field-input" type="number" min="0" step="1" value={form.performer_fixed_fee} onChange={(event) => setForm({ ...form, performer_fixed_fee: event.target.value })} />
          </label>
          <label className="field">
            <span>Tervezett egyéb költség</span>
            <input className="field-input" type="number" min="0" step="1" value={form.event_cost_amount} onChange={(event) => setForm({ ...form, event_cost_amount: event.target.value })} />
          </label>
        </div>
        <label className="field">
          <span>Megjegyzés</span>
          <textarea className="field-input" rows={3} value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} />
        </label>
        {saveMutation.error ? <p className="error-message">{saveMutation.error.message}</p> : null}
        <div className="catalog-editor-actions">
          <Button type="submit">{saveMutation.isPending ? "Mentés..." : "Mentés"}</Button>
          <Button type="button" variant="secondary" onClick={() => {
            setIsCreating(false);
            setForm(buildForm());
          }}>
            Mégsem
          </Button>
        </div>
      </form>
    </Card>
  ) : null;

  return (
    <section className="page-section events-page">
      {isPlanner ? (
        <div className="finance-summary-grid">
          <article className="finance-summary-card">
            <span>Tervezett / aktív esemény</span>
            <strong>{plannedEvents.length}</strong>
          </article>
          <article className="finance-summary-card">
            <span>Következő esemény</span>
            <strong>{nextEvent ? formatDateTime(nextEvent.starts_at) : "-"}</strong>
          </article>
          <article className="finance-summary-card">
            <span>Időjárás kontextus</span>
            <strong>Szolnok cache</strong>
          </article>
        </div>
      ) : (
        <div className="finance-summary-grid">
          <article className="finance-summary-card">
            <span>Események</span>
            <strong>{eventPerformances.length}</strong>
          </article>
          <article className="finance-summary-card">
            <span>Kapcsolt jegybevétel</span>
            <strong>{formatMoney(summary.ticketRevenue)}</strong>
          </article>
          <article className="finance-summary-card">
            <span>Flow saját eredmény</span>
            <strong>{formatMoney(summary.profit)}</strong>
          </article>
          <article className="finance-summary-card">
            <span>Kapcsolt nyugták</span>
            <strong>{formatNumber(summary.receiptCount)}</strong>
          </article>
          <article className="finance-summary-card compact-title">
            <span>Legfelkapottabb</span>
            <strong>
              {mostPopularPerformance
                ? eventById.get(mostPopularPerformance.event_id)?.title ?? "Ismeretlen"
                : "-"}
            </strong>
          </article>
          <article className="finance-summary-card compact-title">
            <span>Legnagyobb forgalom</span>
            <strong>
              {highestRevenuePerformance
                ? eventById.get(highestRevenuePerformance.event_id)?.title ?? "Ismeretlen"
                : "-"}
            </strong>
          </article>
        </div>
      )}

      {isPlanner ? (
        <Card
          tone="rainbow"
          className="event-calendar-card"
          eyebrow="Flow naptár"
          title={formatMonthLabel(calendarAnchor)}
          subtitle="Az esemény időablaka alapján később automatikusan kapcsolódhatnak a jegy-, bár- és időjárási adatok."
          count={`${events.length} esemény`}
        >
          <div className="event-calendar-weekdays">
            {["H", "K", "Sze", "Cs", "P", "Szo", "V"].map((day) => (
              <span key={day}>{day}</span>
            ))}
          </div>
          <div className="event-calendar-grid">
            {calendarDays.map((day) => (
              <article
                className={[
                  "event-calendar-day",
                  day.isCurrentMonth ? "" : "muted",
                  day.isToday ? "today" : "",
                  day.events.length > 0 ? "has-event" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                key={day.key}
              >
                <span className="event-calendar-day-number">{day.dayNumber}</span>
                <div className="event-calendar-day-events">
                  {day.events.slice(0, 3).map((event) => (
                    <button
                      className="event-calendar-pill"
                      key={event.id}
                      type="button"
                      onClick={() => setExpandedEventId(event.id)}
                    >
                      <span>{formatShortTime(event.starts_at)}</span>
                      <strong>{event.title}</strong>
                    </button>
                  ))}
                  {day.events.length > 3 ? (
                    <small>+{day.events.length - 3} további</small>
                  ) : null}
                </div>
              </article>
            ))}
          </div>
        </Card>
      ) : (
        <Card
          tone="rainbow"
          hoverable
          className="flow-performer-ranking-card"
          eyebrow="Fellépők"
          title="Fellépő rangsor"
          subtitle="Kapcsolt POS sorokból számolt, időszakos vagy all-time Flow teljesítmény"
          count={periodOptions.find((option) => option.value === selectedPeriod)?.label ?? "All-time"}
        >
          {performerRows.length > 0 ? (
            <div className="flow-performer-list">
              {performerRows.slice(0, 8).map((row, index) => (
                <article className="flow-performer-card" key={row.performer}>
                  <span>#{index + 1} {row.performer}</span>
                  <strong>{formatMoney(row.profit)}</strong>
                  <small>
                    {row.eventCount} event · saját bevétel {formatMoney(row.ownRevenue)} · jegy{" "}
                    {formatMoney(row.ticketRevenue)} · bár {formatMoney(row.barRevenue)}
                  </small>
                </article>
              ))}
            </div>
          ) : (
            <p className="empty-message">
              Nincs kapcsolt POS alapú fellépői rangsor az aktuális szűrésben. Amint az event időablakába
              érkezik CSV vagy API eladás, az elemző ezt már onnan számolja.
            </p>
          )}
        </Card>
      )}

      {!isPlanner && topPerformance ? (
        <Card
          className="flow-event-performance-card"
          eyebrow="Esemény elemző"
          title="Legerősebb kapcsolt event"
          subtitle="A rangsor a mentett POS sorokból, nem kézi bevételi mezőből számol."
          count={formatMoney(topPerformance.event_profit_lite)}
        >
          <div className="flow-event-top">
            <div>
              <span>{eventById.get(topPerformance.event_id)?.performer_name ?? "Fellépő nélkül"}</span>
              <strong>{eventById.get(topPerformance.event_id)?.title ?? "Ismeretlen esemény"}</strong>
              <small>{formatDateTime(topPerformance.starts_at)} · {formatEventWeatherSummary(topPerformance)}</small>
            </div>
            <div>
              <span>Jegy / bár</span>
              <strong>
                {formatMoney(topPerformance.ticket_revenue_gross)} / {formatMoney(topPerformance.bar_revenue_gross)}
              </strong>
              <small>{topPerformance.source_row_count} POS sor · {topPerformance.receipt_count} nyugta</small>
            </div>
          </div>
        </Card>
      ) : null}

      {!isPlanner ? (
        <Card
          className="event-comparison-card"
          eyebrow="Összehasonlítás"
          title="Event teljesítmény rangsor"
          subtitle="Kapcsolt POS sorokból számolt profit, jegy-bár mix és időjárási kontextus."
          count={`${comparisonRows.length} event`}
        >
          {eventPerformancesQuery.isLoading ? (
            <p className="info-message">Event performance adatok betöltése...</p>
          ) : null}
          {eventPerformancesQuery.error ? (
            <p className="error-message">{eventPerformancesQuery.error.message}</p>
          ) : null}
          {comparisonRows.length > 0 ? (
            <div className="event-comparison-list">
              {comparisonRows.map((performance, index) => {
                const event = eventById.get(performance.event_id);
                const ticketShare = getTicketSharePercent(performance);
                const barShare = Math.max(0, 100 - ticketShare);
                return (
                  <button
                    className="event-comparison-row"
                    key={performance.event_id}
                    type="button"
                    onClick={() => setExpandedEventId(performance.event_id)}
                  >
                    <span className="event-comparison-rank">{index + 1}</span>
                    <div className="event-comparison-main">
                      <strong>{event?.title ?? "Ismeretlen esemény"}</strong>
                      <small>
                        {event?.performer_name ?? "Fellépő nélkül"} · {formatDateTime(performance.starts_at)}
                      </small>
                    </div>
                    <div className="event-comparison-money">
                      <strong>{formatMoney(performance.event_profit_lite)}</strong>
                      <small>
                        Jegy {formatMoney(performance.ticket_revenue_gross)} · Bár{" "}
                        {formatMoney(performance.bar_revenue_gross)}
                      </small>
                    </div>
                    <div className="event-comparison-mix" aria-label="Jegy és bár arány">
                      <span>
                        <i style={{ width: `${Math.min(100, Math.max(0, ticketShare))}%` }} />
                      </span>
                      <small>
                        Jegy {formatPercent(ticketShare)}% · Bár {formatPercent(barShare)}%
                      </small>
                    </div>
                    <div className="event-comparison-weather">
                      <strong>{getWeatherImpactLabel(performance)}</strong>
                      <small>
                        {performance.weather.average_temperature_c
                          ? `${formatNumber(performance.weather.average_temperature_c)} °C`
                          : "Nincs átlaghőmérséklet"}{" "}
                        · {performance.receipt_count} nyugta
                      </small>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <p className="empty-message">
              Még nincs összehasonlítható kapcsolt performance adat az aktuális szűrésben.
            </p>
          )}
        </Card>
      ) : null}

      {formPanel}
      {eventsQuery.isLoading ? <p className="info-message">Események betöltése...</p> : null}
      {eventsQuery.error ? <p className="error-message">{eventsQuery.error.message}</p> : null}

      <div className="event-card-grid">
        {events.map((event) => {
          const expanded = expandedEventId === event.id;
          const rowPerformance = performanceByEventId.get(event.id);
          const performance =
            expanded && eventPerformanceQuery.data?.event_id === event.id
              ? eventPerformanceQuery.data
              : rowPerformance ?? null;
          const weatherCoverage = weatherCoverageByEventId[event.id];
          const isEnsuringWeather =
            weatherCoverageMutation.isPending &&
            weatherCoverageMutation.variables === event.id;
          const displayedTicketRevenue =
            !isPlanner && rowPerformance ? rowPerformance.ticket_revenue_gross : event.ticket_revenue_gross;
          const displayedBarRevenue =
            !isPlanner && rowPerformance ? rowPerformance.bar_revenue_gross : event.bar_revenue_gross;
          const displayedProfit =
            !isPlanner && rowPerformance ? rowPerformance.event_profit_lite : event.event_profit_lite;
          return (
            <Card
              key={event.id}
              hoverable
              className={expanded ? "event-card event-card-open" : "event-card"}
              eyebrow={formatStatus(event.status)}
              title={event.title}
              subtitle={event.performer_name ?? "Fellépő később rögzíthető"}
              count={formatDateTime(event.starts_at)}
              onClick={() => setExpandedEventId(expanded ? null : event.id)}
            >
              <div className="event-metrics">
                {isPlanner ? (
                  <>
                    <span>Kezdés <strong>{formatDateTime(event.starts_at)}</strong></span>
                    <span>Zárás <strong>{formatDateTime(event.ends_at)}</strong></span>
                    <span>Részesedés <strong>{formatNumber(event.performer_share_percent)}%</strong></span>
                  </>
                ) : (
                  <>
                    <span>Jegy <strong>{formatMoney(displayedTicketRevenue)}</strong></span>
                    <span>Bár <strong>{formatMoney(displayedBarRevenue)}</strong></span>
                    <span>Saját eredmény <strong>{formatMoney(displayedProfit)}</strong></span>
                  </>
                )}
              </div>
              {expanded ? (
                <div className="catalog-details" onClick={(clickEvent) => clickEvent.stopPropagation()}>
                  <div className="event-settlement-grid">
                    <article className="catalog-decision-card primary">
                      <span>Teljes bevétel</span>
                      <strong>{formatMoney(toNumber(displayedTicketRevenue) + toNumber(displayedBarRevenue))}</strong>
                      <small>{isPlanner ? "Tervezési rekord szerinti bevétel." : "Kapcsolt POS sorok alapján."}</small>
                    </article>
                    <article className="catalog-decision-card warning">
                      <span>Fellépő része</span>
                      <strong>{formatMoney(performance?.performer_share_amount ?? event.performer_share_amount)}</strong>
                      <small>{formatNumber(event.performer_share_percent)}% jegybevétel alapján, fix díj nélkül.</small>
                    </article>
                    <article className="catalog-decision-card success">
                      <span>Flow saját bevétel</span>
                      <strong>{formatMoney(performance?.own_revenue ?? event.own_revenue)}</strong>
                      <small>Megtartott jegybevétel plusz bárbevétel.</small>
                    </article>
                    <article className="catalog-decision-card neutral">
                      <span>Event profit lite</span>
                      <strong>{formatMoney(displayedProfit)}</strong>
                      <small>Saját bevétel mínusz fix fellépti díj és event költség.</small>
                    </article>
                  </div>
                  <div className="event-ticket-actual-panel">
                    <div className="event-live-heading">
                      <span>Jegyadatok</span>
                      <strong>Külön ticket rendszerből rögzített actual</strong>
                    </div>
                    <div className="form-grid">
                      <label className="field">
                        <span>Forrás</span>
                        <input
                          className="field-input"
                          value={ticketActualForm.source_name}
                          onChange={(inputEvent) =>
                            setTicketActualForm({ ...ticketActualForm, source_name: inputEvent.target.value })
                          }
                          placeholder="Ticket rendszer neve"
                        />
                      </label>
                      <label className="field">
                        <span>Forrás azonosító</span>
                        <input
                          className="field-input"
                          value={ticketActualForm.source_reference}
                          onChange={(inputEvent) =>
                            setTicketActualForm({ ...ticketActualForm, source_reference: inputEvent.target.value })
                          }
                        />
                      </label>
                      <label className="field">
                        <span>Eladott jegy</span>
                        <input
                          className="field-input"
                          type="number"
                          min="0"
                          step="1"
                          value={ticketActualForm.sold_quantity}
                          onChange={(inputEvent) =>
                            setTicketActualForm({ ...ticketActualForm, sold_quantity: inputEvent.target.value })
                          }
                        />
                      </label>
                      <label className="field">
                        <span>Bruttó jegybevétel</span>
                        <input
                          className="field-input"
                          type="number"
                          min="0"
                          step="1"
                          value={ticketActualForm.gross_revenue}
                          onChange={(inputEvent) =>
                            setTicketActualForm({ ...ticketActualForm, gross_revenue: inputEvent.target.value })
                          }
                        />
                      </label>
                      <label className="field">
                        <span>Nettó jegybevétel</span>
                        <input
                          className="field-input"
                          type="number"
                          min="0"
                          step="1"
                          value={ticketActualForm.net_revenue}
                          onChange={(inputEvent) =>
                            setTicketActualForm({ ...ticketActualForm, net_revenue: inputEvent.target.value })
                          }
                        />
                      </label>
                      <label className="field">
                        <span>ÁFA összeg</span>
                        <input
                          className="field-input"
                          type="number"
                          min="0"
                          step="1"
                          value={ticketActualForm.vat_amount}
                          onChange={(inputEvent) =>
                            setTicketActualForm({ ...ticketActualForm, vat_amount: inputEvent.target.value })
                          }
                        />
                      </label>
                      <label className="field">
                        <span>ÁFA kulcs</span>
                        <select
                          className="field-input"
                          value={ticketActualForm.vat_rate_id}
                          onChange={(inputEvent) =>
                            setTicketActualForm({ ...ticketActualForm, vat_rate_id: inputEvent.target.value })
                          }
                        >
                          <option value="">Nincs kiválasztva</option>
                          {vatRates.map((vatRate) => (
                            <option key={vatRate.id} value={vatRate.id}>
                              {vatRate.name}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label className="field">
                        <span>Platform díj bruttó</span>
                        <input
                          className="field-input"
                          type="number"
                          min="0"
                          step="1"
                          value={ticketActualForm.platform_fee_gross}
                          onChange={(inputEvent) =>
                            setTicketActualForm({ ...ticketActualForm, platform_fee_gross: inputEvent.target.value })
                          }
                        />
                      </label>
                      <label className="field">
                        <span>Riport dátuma</span>
                        <input
                          className="field-input"
                          type="datetime-local"
                          value={ticketActualForm.reported_at}
                          onChange={(inputEvent) =>
                            setTicketActualForm({ ...ticketActualForm, reported_at: inputEvent.target.value })
                          }
                        />
                      </label>
                    </div>
                    <label className="field">
                      <span>Jegy megjegyzés</span>
                      <textarea
                        className="field-input"
                        rows={2}
                        value={ticketActualForm.notes}
                        onChange={(inputEvent) =>
                          setTicketActualForm({ ...ticketActualForm, notes: inputEvent.target.value })
                        }
                      />
                    </label>
                    {ticketActualQuery.isLoading ? (
                      <p className="info-message">Jegyadatok betöltése...</p>
                    ) : null}
                    {ticketActualMutation.error ? (
                      <p className="error-message">{ticketActualMutation.error.message}</p>
                    ) : null}
                    <div className="catalog-editor-actions">
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={() => saveTicketActual(event.id)}
                        disabled={ticketActualMutation.isPending}
                      >
                        {ticketActualMutation.isPending ? "Jegyadat mentése..." : "Jegyadat mentése"}
                      </Button>
                    </div>
                  </div>
                  {eventPerformanceQuery.isLoading && expanded ? (
                    <p className="info-message">Event teljesítmény betöltése...</p>
                  ) : null}
                  {eventPerformanceQuery.error && expanded ? (
                    <p className="error-message">{eventPerformanceQuery.error.message}</p>
                  ) : null}
                  {performance ? (
                    <div className="event-live-performance">
                      <div className="event-live-heading">
                        <span>Időablak alapján kapcsolt adatok</span>
                        <strong>{performance.source_row_count} POS sor · {performance.receipt_count} nyugta</strong>
                      </div>
                      <div className="event-settlement-grid">
                        <article className="catalog-decision-card primary">
                          <span>Kapcsolt jegybevétel</span>
                          <strong>{formatMoney(performance.ticket_revenue_gross)}</strong>
                          <small>{formatNumber(performance.ticket_quantity)} jegy jellegű mennyiség.</small>
                        </article>
                        <article className="catalog-decision-card success">
                          <span>Kapcsolt bárbevétel</span>
                          <strong>{formatMoney(performance.bar_revenue_gross)}</strong>
                          <small>{formatNumber(performance.bar_quantity)} fogyasztási mennyiség.</small>
                        </article>
                        <article className="catalog-decision-card warning">
                          <span>Előadói rész</span>
                          <strong>{formatMoney(performance.performer_share_amount)}</strong>
                          <small>{formatNumber(performance.performer_share_percent)}% a kapcsolt jegybevételből.</small>
                        </article>
                        <article className="catalog-decision-card neutral">
                          <span>Időjárás</span>
                          <strong>{formatEventWeatherSummary(performance)}</strong>
                          <small>{performance.weather.observation_count} órás Szolnok megfigyelés.</small>
                        </article>
                      </div>
                      <div className="event-weather-coverage-panel">
                        <div>
                          <span>Időjárási adatok</span>
                          <strong>{formatWeatherCoverageLabel(performance, weatherCoverage)}</strong>
                          <small>{formatWeatherCoverageHelp(performance, weatherCoverage)}</small>
                        </div>
                        <Button
                          type="button"
                          variant="secondary"
                          onClick={() => weatherCoverageMutation.mutate(event.id)}
                          disabled={isEnsuringWeather}
                        >
                          {isEnsuringWeather ? "Ellenőrzés..." : "Időjárás ellenőrzése"}
                        </Button>
                      </div>
                      <div className="event-performance-lists">
                        <div>
                          <span>Kategóriák</span>
                          {performance.categories.slice(0, 5).map((category) => (
                            <article className="event-performance-row" key={category.category_name}>
                              <strong>{category.category_name}</strong>
                              <small>{formatMoney(category.gross_amount)} · {formatNumber(category.quantity)} mennyiség</small>
                            </article>
                          ))}
                        </div>
                        <div>
                          <span>Top tételek</span>
                          {performance.top_products.slice(0, 5).map((product) => (
                            <article className="event-performance-row" key={`${product.product_name}-${product.category_name}`}>
                              <strong>{product.product_name}</strong>
                              <small>{formatMoney(product.gross_amount)} · {product.category_name}</small>
                            </article>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : null}
                  <div className="catalog-product-action-bar">
                    <div>
                      <span>Event műveletek</span>
                      <strong>{event.is_active ? "Aktív összehasonlítási alap" : "Archivált esemény"}</strong>
                    </div>
                    <div className="catalog-editor-actions">
                      <Button type="button" variant="secondary" onClick={() => startEdit(event)}>Szerkesztés</Button>
                      <Button type="button" variant="secondary" onClick={() => archiveMutation.mutate(event.id)} disabled={archiveMutation.isPending}>Archiválás</Button>
                    </div>
                  </div>
                  <div className="details-grid">
                    <article className="detail-item"><span>Kezdés</span><strong>{formatDateTime(event.starts_at)}</strong></article>
                    <article className="detail-item"><span>Zárás</span><strong>{formatDateTime(event.ends_at)}</strong></article>
                    <article className="detail-item"><span>Várt létszám</span><strong>{event.expected_attendance ?? "-"}</strong></article>
                    <article className="detail-item"><span>Fix fellépti díj</span><strong>{formatMoney(event.performer_fixed_fee)}</strong></article>
                    <article className="detail-item"><span>Egyéb költség</span><strong>{formatMoney(event.event_cost_amount)}</strong></article>
                    <article className="detail-item"><span>Megjegyzés</span><strong>{event.notes ?? "-"}</strong></article>
                  </div>
                </div>
              ) : null}
            </Card>
          );
        })}
      </div>

      {events.length === 0 && !eventsQuery.isLoading ? (
        <p className="empty-message">Nincs még rögzített esemény ehhez a nézethez.</p>
      ) : null}
    </section>
  );
}
