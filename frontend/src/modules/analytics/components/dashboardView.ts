import type {
  DashboardBreakdownRow,
  DashboardData,
  DashboardHeatmapCell,
  DashboardKpi,
  DashboardPeriodPreset,
  DashboardScope,
} from "../types/analytics";

export const scopeOptions: Array<{ value: DashboardScope; label: string }> = [
  { value: "overall", label: "Összesített" },
  { value: "flow", label: "Flow" },
  { value: "gourmand", label: "Gourmand" },
];

export const periodOptions: Array<{
  value: DashboardPeriodPreset;
  label: string;
}> = [
  { value: "last_1_hour", label: "1 óra" },
  { value: "last_6_hours", label: "6 óra" },
  { value: "last_12_hours", label: "12 óra" },
  { value: "today", label: "Ma" },
  { value: "week", label: "Ez a hét" },
  { value: "month", label: "Ez a hónap" },
  { value: "last_30_days", label: "Elmúlt 30 nap" },
  { value: "year", label: "Ez az év" },
  { value: "custom", label: "Egyedi" },
];

export const kpiHelp: Record<string, string> = {
  revenue: "Bruttó bevétel a kiválasztott időszak eladási tranzakcióiból.",
  cost: "Rögzített kiadások és költségoldali tranzakciók a kiválasztott időszakban.",
  profit: "Kontrolling profit: bevétel mínusz rögzített kiadás.",
  transaction_count: "A kiválasztott időszak pénzügyi tranzakcióinak száma.",
  average_basket_value: "Átlagos nyugtaérték a rögzített eladások alapján.",
  average_basket_quantity: "Egy nyugtára jutó átlagos eladott mennyiség.",
};

export const mixPalette = [
  "#8b5cf6",
  "#d946ef",
  "#38bdf8",
  "#34d399",
  "#f59e0b",
  "#fb7185",
  "#a78bfa",
  "#22d3ee",
];

const kpiLabels: Record<string, string> = {
  revenue: "Bevétel",
  cost: "Kiadás",
  profit: "Profit",
  transaction_count: "Tranzakciók",
  average_basket_value: "Átlagkosár érték",
  average_basket_quantity: "Átlagkosár mennyiség",
};

const visibleKpiCodes = [
  "revenue",
  "cost",
  "profit",
  "transaction_count",
  "average_basket_value",
  "average_basket_quantity",
];

export const heatmapWeekdays = ["Hét", "Ked", "Sze", "Csü", "Pén", "Szo", "Vas"];

export function toNumber(value: string | number) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function formatMoney(value: string | number) {
  return new Intl.NumberFormat("hu-HU", {
    style: "currency",
    currency: "HUF",
    maximumFractionDigits: 0,
  }).format(typeof value === "number" ? value : toNumber(value));
}

export function formatNumber(value: string | number) {
  return new Intl.NumberFormat("hu-HU", {
    maximumFractionDigits: 1,
  }).format(typeof value === "number" ? value : toNumber(value));
}

export function formatOptionalPercent(
  value: string | number | null | undefined,
) {
  return value === null || value === undefined ? "-" : `${formatNumber(value)}%`;
}

export function exportDashboardData(dashboard: DashboardData | null) {
  if (!dashboard) return;
  const fileName = `biztracker-${dashboard.scope}-${dashboard.period.start_date}-${dashboard.period.end_date}.json`;
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(dashboard, null, 2)], {
      type: "application/json;charset=utf-8",
    }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(url);
}

export function formatTrendDate(
  value: string,
  grain: "hour" | "day" | "month",
  detail = false,
) {
  const date = new Date(value);
  if (grain === "hour") {
    return new Intl.DateTimeFormat("hu-HU", {
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  }
  if (grain === "month") {
    return new Intl.DateTimeFormat("hu-HU", {
      year: detail ? "numeric" : undefined,
      month: "short",
    }).format(date);
  }
  return new Intl.DateTimeFormat("hu-HU", {
    month: "short",
    day: "2-digit",
  }).format(date);
}

export function formatGrain(value: string) {
  return (
    { hour: "Órás bontás", month: "Havi bontás", day: "Napi bontás" }[value] ??
    "Időszaki bontás"
  );
}

export function formatSourceLayer(value: string) {
  const labels: Record<string, string> = {
    weather_enriched_import: "Időjárással összekapcsolt eladási adat",
    financial_actual: "Rögzített pénzügyi adat",
    derived_actual: "Számított pénzügyi mutató",
    import_derived: "Importált eladási adat",
    recipe_or_unit_cost: "Becsült termékköltség",
    catalog_inventory_actual: "Katalógus és készletadat",
    inventory_actual: "Készletmozgásból számolt adat",
  };
  return labels[value] ?? "Adatbázisban rögzített adat";
}

export function formatAmountBasis(value: string | null | undefined) {
  const labels: Record<string, string> = {
    gross: "Bruttó",
    net: "Nettó",
    vat: "ÁFA",
    mixed: "Vegyes alap",
  };
  return value ? labels[value] ?? value : null;
}

export function formatAmountOrigin(value: string | null | undefined) {
  const labels: Record<string, string> = {
    actual: "tényleges",
    derived: "számított",
  };
  return value ? labels[value] ?? value : null;
}

export function formatAmountMarker(
  basis: string | null | undefined,
  origin: string | null | undefined,
) {
  return [formatAmountBasis(basis), formatAmountOrigin(origin)]
    .filter(Boolean)
    .join(" · ");
}

export function formatTaxBreakdownSource(value: string | null | undefined) {
  const labels: Record<string, string> = {
    supplier_invoice_actual: "Számla alapján bontott",
    partial_supplier_invoice_actual: "Részben számla alapján bontott",
    product_vat_derived: "Termék ÁFA-kulcsból számolt",
    partial_product_vat_derived: "Részben termék ÁFA-kulcsból számolt",
    not_available: "Nincs ÁFA-bontás",
  };
  return value ? labels[value] ?? value : "Nincs ÁFA-bontás";
}

export function formatVatReadinessStatus(value: string) {
  return (
    {
      complete: "Teljes",
      partial: "Hiányos",
      missing: "Nincs lefedve",
      no_data: "Nincs adat",
    }[value] ?? value
  );
}

export function formatCostSource(value: string | null | undefined) {
  const labels: Record<string, string> = {
    recipe_or_unit_cost: "Recept/default nettó költség",
    partial_recipe_or_unit_cost: "Részben ismert nettó költség",
    not_available: "Nincs költségalap",
  };
  return value ? labels[value] ?? value : "Nincs költségalap";
}

export function formatMarginStatus(value: string | null | undefined) {
  const labels: Record<string, string> = {
    complete: "Teljes margin",
    partial: "Részleges margin",
    missing_vat_rate: "Hiányzó ÁFA-kulcs",
    missing_cost: "Hiányzó költség",
    missing_vat_and_cost: "Hiányzó ÁFA és költség",
    no_data: "Nincs adat",
    not_available: "Nem számolható",
  };
  return value ? labels[value] ?? value : "Nem számolható";
}

export function formatTransactionType(value: string) {
  const labels: Record<string, string> = {
    supplier_invoice: "Beszerzési számla",
    manual_expense: "Kézi költségrögzítés",
    pos_sale: "Kasszás értékesítés",
    expense: "Kiadás",
  };
  return labels[value] ?? value.replaceAll("_", " ");
}

export function formatSourceType(value: string) {
  const labels: Record<string, string> = {
    supplier_invoice: "Beszerzési számla",
    supplier_invoice_line: "Beszerzési számlasor",
    import_row: "Importált kasszasor",
    manual_entry: "Kézi rögzítés",
  };
  return labels[value] ?? formatSourceLayer(value);
}

export function formatPaymentMethod(value: string) {
  const labels: Record<string, string> = {
    cash: "Készpénz",
    card: "Bankkártya",
    szep: "SZÉP kártya",
    szep_card: "SZÉP kártya",
    transfer: "Átutalás",
    unknown: "Ismeretlen fizetés",
  };
  return labels[value.toLowerCase()] ?? value.replaceAll("_", " ");
}

export function formatWeatherCondition(value: string) {
  const labels: Record<string, string> = {
    napos: "Napos",
    reszben_felhos: "Részben felhős",
    borult: "Borult",
    kodos: "Ködös",
    esos: "Esős",
    havas: "Havas",
    szeles: "Szeles",
    viharos: "Viharos",
    ismeretlen: "Ismeretlen",
  };
  return labels[value] ?? value.replaceAll("_", " ");
}

export function formatTemperatureBand(value: string) {
  return (
    { hideg: "Hideg", enyhe: "Enyhe", meleg: "Meleg", kanikula: "Kánikula" }[
      value
    ] ?? value.replaceAll("_", " ")
  );
}

export function formatWeatherConditionBand(value: string) {
  const labels: Record<string, string> = {
    napos_szaraz: "Napos, száraz",
    reszben_felhos: "Részben felhős",
    borult: "Borult",
    csapadekos: "Csapadékos",
  };
  return labels[value] ?? value.replaceAll("_", " ");
}

export function formatForecastDate(value: string) {
  return new Intl.DateTimeFormat("hu-HU", {
    weekday: "short",
    month: "short",
    day: "2-digit",
  }).format(new Date(`${value}T12:00:00`));
}

export function formatForecastConfidence(value: string) {
  return (
    {
      magas: "Magas bizalom",
      kozepes: "Közepes bizalom",
      alacsony: "Alacsony bizalom",
    }[value] ?? value
  );
}

export function formatDemandSignal(value: string) {
  return (
    {
      emelkedo: "Emelkedő kereslet",
      normal: "Normál kereslet",
      visszafogott: "Visszafogott kereslet",
    }[value] ?? value
  );
}

export function formatReadinessLevel(value: string) {
  return (
    { rendben: "Rendben", figyelendo: "Figyelendő", kritikus: "Kritikus" }[
      value
    ] ?? value
  );
}

export function formatBasketValueBand(value: string) {
  const labels: Record<string, string> = {
    "0-999": "0-999 Ft",
    "1000-2499": "1 000-2 499 Ft",
    "2500-4999": "2 500-4 999 Ft",
    "5000-9999": "5 000-9 999 Ft",
    "10000+": "10 000 Ft felett",
  };
  return labels[value] ?? value;
}

export function formatHeatmapHour(hour: number) {
  return `${String(hour).padStart(2, "0")}:00`;
}

export function formatEventDate(value: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("hu-HU", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function getTopCategory(rows: DashboardBreakdownRow[]) {
  return [...rows].sort(
    (left, right) => toNumber(right.revenue) - toNumber(left.revenue),
  )[0];
}

export function getStrongestHeatmapCell(cells: DashboardHeatmapCell[]) {
  return [...cells].sort(
    (left, right) => toNumber(right.revenue) - toNumber(left.revenue),
  )[0];
}

export function getWeekdayLabel(value: number) {
  return heatmapWeekdays[value] ?? "-";
}

export function getKpiLabel(kpi: DashboardKpi) {
  return kpiLabels[kpi.code] ?? kpi.label;
}

export function getVisibleKpis(kpis: DashboardKpi[]) {
  return visibleKpiCodes
    .map((code) => kpis.find((kpi) => kpi.code === code))
    .filter((kpi): kpi is DashboardKpi => Boolean(kpi));
}

export function getKpiValue(kpi: DashboardKpi) {
  if (kpi.unit === "HUF") return formatMoney(kpi.value);
  if (kpi.unit === "%") return `${formatNumber(kpi.value)}%`;
  return formatNumber(kpi.value);
}

export function getKpiSecondary(kpi: DashboardKpi, allKpis: DashboardKpi[]) {
  if (kpi.code === "revenue") {
    const transactions = allKpis.find((item) => item.code === "transaction_count");
    return transactions ? `${formatNumber(transactions.value)} tranzakció` : null;
  }
  if (kpi.code === "cost") {
    const cogs = allKpis.find((item) => item.code === "estimated_cogs");
    return cogs ? `Becsült eladott áruk költsége: ${formatMoney(cogs.value)}` : null;
  }
  if (kpi.code === "profit") {
    const profit = allKpis.find((item) => item.code === "profit_margin");
    const percent = allKpis.find((item) => item.code === "gross_margin_percent");
    if (profit && percent) {
      return `Árrés profit: ${formatMoney(profit.value)} · ${formatNumber(percent.value)}%`;
    }
    return profit ? `Árrés profit: ${formatMoney(profit.value)}` : null;
  }
  if (kpi.code === "transaction_count") {
    const basket = allKpis.find((item) => item.code === "average_basket_value");
    return basket ? `Átlagkosár: ${formatMoney(basket.value)}` : null;
  }
  return null;
}

export function getKpiTone(code: string) {
  if (code === "revenue") return "primary" as const;
  if (code === "cost") return "secondary" as const;
  if (code === "profit") return "highlight" as const;
  if (code === "profit_margin" || code === "average_basket_value") {
    return "secondary" as const;
  }
  return "rainbow" as const;
}
