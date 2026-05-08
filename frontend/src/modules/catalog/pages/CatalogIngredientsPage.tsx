import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useTopbarControls } from "../../../shared/components/layout/TopbarControlsContext";
import { Button } from "../../../shared/components/ui/Button";
import { Card } from "../../../shared/components/ui/Card";
import { routes } from "../../../shared/constants/routes";
import { listBusinessUnits, listUnitsOfMeasure, listVatRates } from "../../masterData/api/masterDataApi";
import {
  createInventoryMovement,
  listEstimatedConsumptionAudit,
  listInventoryMovements,
  listInventoryStockLevels,
  listInventoryTheoreticalStock,
} from "../../inventory/api/inventoryApi";
import type { InventoryMovementCreatePayload } from "../../inventory/types/inventory";
import {
  createCatalogIngredient,
  deleteCatalogIngredient,
  listCatalogIngredients,
  updateCatalogIngredient,
} from "../api/catalogApi";
import type { CatalogIngredient, CatalogIngredientPayload } from "../types/catalog";

type IngredientSort = "abc" | "cost" | "stock" | "usage";
type IngredientFormState = {
  id?: string;
  name: string;
  item_type: string;
  uom_id: string;
  default_vat_rate_id: string;
  track_stock: boolean;
  default_unit_cost: string;
  estimated_stock_quantity: string;
  is_active: boolean;
};
type MovementFormState = {
  movement_type: "purchase" | "adjustment" | "waste" | "initial_stock";
  quantity: string;
  unit_cost: string;
  note: string;
};

const INITIAL_MOVEMENT_FORM: MovementFormState = {
  movement_type: "purchase",
  quantity: "",
  unit_cost: "",
  note: "",
};

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

function formatDateTime(value: string | null) {
  if (!value) {
    return "-";
  }

  return new Intl.DateTimeFormat("hu-HU", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatQuantity(value: string | number | null | undefined, unit = "") {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  const formattedValue = formatNumber(value);
  return unit ? `${formattedValue} ${unit}` : formattedValue;
}

function formatItemType(value: string) {
  const labels: Record<string, string> = {
    raw_material: "Alapanyag",
    packaging: "Csomagolóanyag",
    finished_good: "Késztermék",
    semi_finished: "Félkész termék",
  };
  return labels[value] ?? value;
}

function formatMovementType(value: string) {
  const labels: Record<string, string> = {
    purchase: "Beszerzés",
    adjustment: "Korrekció",
    waste: "Selejt",
    initial_stock: "Nyitókészlet",
  };
  return labels[value] ?? value;
}

function formatEstimationBasis(value: string) {
  const labels: Record<string, string> = {
    recipe: "Recept alapján",
    direct_item: "Direkt készletelem",
    not_configured: "Nincs beállítva",
  };
  return labels[value] ?? value;
}

function formatSourceType(value: string) {
  const labels: Record<string, string> = {
    pos_receipt: "Nyugta",
    import_row: "Importált POS sor",
    demo_pos_receipt: "Demo kassza",
  };
  return labels[value] ?? value;
}

function formatCostSourceType(value: string | null) {
  const labels: Record<string, string> = {
    supplier_invoice_line: "Beszerzesi szamlasor",
    manual: "Kezi beallitas",
  };
  return value ? labels[value] ?? value : "Nincs forras";
}

function getIngredientCostHealth(ingredient: CatalogIngredient) {
  if (!ingredient.default_unit_cost) {
    return {
      label: "Beszerzesi koltseg hianyzik",
      className: "status-pill status-pill-danger",
    };
  }

  if (ingredient.default_unit_cost_source_type === "supplier_invoice_line") {
    return {
      label: "Szamlabol frissult",
      className: "status-pill status-pill-success",
    };
  }

  if (ingredient.default_unit_cost_source_type === "manual") {
    return {
      label: "Kezi koltseg",
      className: "status-pill",
    };
  }

  return {
    label: "Koltseg forras nelkul",
    className: "status-pill status-pill-warning",
  };
}

function getIngredientHealth({
  trackStock,
  estimatedStockQuantity,
  actualQuantity,
  varianceQuantity,
}: {
  trackStock: boolean;
  estimatedStockQuantity: string | null;
  actualQuantity?: string;
  varianceQuantity?: string | null;
}) {
  if (!trackStock) {
    return {
      label: "Nem készletkövetett",
      className: "status-pill",
    };
  }

  if (estimatedStockQuantity === null || toNumber(estimatedStockQuantity) <= 0) {
    return {
      label: "Becsült készlet hiányzik",
      className: "status-pill status-pill-danger",
    };
  }

  if (actualQuantity !== undefined && toNumber(actualQuantity) <= 0) {
    return {
      label: "Nincs tényleges készlet",
      className: "status-pill status-pill-danger",
    };
  }

  if (varianceQuantity !== null && varianceQuantity !== undefined && toNumber(varianceQuantity) < 0) {
    return {
      label: "Hiány várható",
      className: "status-pill status-pill-danger",
    };
  }

  return {
    label: "Rendben",
    className: "status-pill status-pill-success",
  };
}

function buildIngredientForm(item?: CatalogIngredient, fallbackUomId = ""): IngredientFormState {
  return {
    id: item?.id,
    name: item?.name ?? "",
    item_type: item?.item_type ?? "raw_material",
    uom_id: item?.uom_id ?? fallbackUomId,
    default_vat_rate_id: item?.default_vat_rate_id ?? "",
    track_stock: item?.track_stock ?? true,
    default_unit_cost: item?.default_unit_cost ?? "",
    estimated_stock_quantity: item?.estimated_stock_quantity ?? "",
    is_active: item?.is_active ?? true,
  };
}

function compactNullable(value: string) {
  return value.trim() === "" ? null : value.trim();
}

function CatalogIngredientsHeaderControls({
  businessUnits,
  selectedBusinessUnitId,
  setSelectedBusinessUnitId,
  search,
  setSearch,
  sort,
  setSort,
  startCreate,
}: {
  businessUnits: Array<{ id: string; name: string }>;
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  search: string;
  setSearch: (value: string) => void;
  sort: IngredientSort;
  setSort: (value: IngredientSort) => void;
  startCreate: () => void;
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
        <span>Keresés</span>
        <input
          className="field-input"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Alapanyag neve"
        />
      </label>

      <label className="field topbar-field">
        <span>Rendezés</span>
        <select
          className="field-input"
          value={sort}
          onChange={(event) => setSort(event.target.value as IngredientSort)}
        >
          <option value="abc">ABC</option>
          <option value="cost">Beszerzési költség</option>
          <option value="stock">Becsült készlet</option>
          <option value="usage">Recept-használat</option>
        </select>
      </label>

      <Button type="button" onClick={startCreate}>
        Új alapanyag
      </Button>
      <Link className="secondary-button" to={routes.catalogProducts}>
        Termékek
      </Link>
    </div>
  );
}

export function CatalogIngredientsPage() {
  const { setControls } = useTopbarControls();
  const queryClient = useQueryClient();
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<IngredientSort>("abc");
  const [expandedIngredientId, setExpandedIngredientId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [form, setForm] = useState<IngredientFormState>(() => buildIngredientForm());
  const [movementForm, setMovementForm] = useState<MovementFormState>(INITIAL_MOVEMENT_FORM);
  const [movementMessage, setMovementMessage] = useState("");
  const [movementErrorMessage, setMovementErrorMessage] = useState("");

  const businessUnitsQuery = useQuery({
    queryKey: ["business-units"],
    queryFn: listBusinessUnits,
  });
  const businessUnits = businessUnitsQuery.data ?? [];

  useEffect(() => {
    if (!selectedBusinessUnitId && businessUnits.length > 0) {
      setSelectedBusinessUnitId(businessUnits[0].id);
    }
  }, [businessUnits, selectedBusinessUnitId]);

  const ingredientsQuery = useQuery({
    queryKey: ["catalog-ingredients", selectedBusinessUnitId],
    queryFn: () => listCatalogIngredients(selectedBusinessUnitId),
    enabled: Boolean(selectedBusinessUnitId),
  });
  const unitsQuery = useQuery({
    queryKey: ["units-of-measure"],
    queryFn: listUnitsOfMeasure,
  });
  const vatRatesQuery = useQuery({
    queryKey: ["vat-rates"],
    queryFn: listVatRates,
  });
  const stockLevelsQuery = useQuery({
    queryKey: ["catalog-stock-levels", selectedBusinessUnitId],
    queryFn: () => listInventoryStockLevels({ business_unit_id: selectedBusinessUnitId }),
    enabled: Boolean(selectedBusinessUnitId),
  });
  const theoreticalStockQuery = useQuery({
    queryKey: ["catalog-theoretical-stock", selectedBusinessUnitId],
    queryFn: () => listInventoryTheoreticalStock({ business_unit_id: selectedBusinessUnitId }),
    enabled: Boolean(selectedBusinessUnitId),
  });
  const selectedIngredientMovementsQuery = useQuery({
    queryKey: ["catalog-ingredient-movements", selectedBusinessUnitId, expandedIngredientId],
    queryFn: () =>
      listInventoryMovements({
        business_unit_id: selectedBusinessUnitId,
        inventory_item_id: expandedIngredientId ?? undefined,
        limit: 8,
      }),
    enabled: Boolean(selectedBusinessUnitId && expandedIngredientId),
  });
  const selectedIngredientAuditQuery = useQuery({
    queryKey: ["catalog-ingredient-consumption-audit", selectedBusinessUnitId, expandedIngredientId],
    queryFn: () =>
      listEstimatedConsumptionAudit({
        business_unit_id: selectedBusinessUnitId,
        inventory_item_id: expandedIngredientId ?? undefined,
        limit: 8,
      }),
    enabled: Boolean(selectedBusinessUnitId && expandedIngredientId),
  });

  const ingredients = ingredientsQuery.data ?? [];
  const units = unitsQuery.data ?? [];
  const vatRates = vatRatesQuery.data ?? [];
  const selectedIngredientMovements = selectedIngredientMovementsQuery.data ?? [];
  const selectedIngredientAuditRows = selectedIngredientAuditQuery.data ?? [];
  const stockLevelByItemId = useMemo(
    () =>
      new Map(
        (stockLevelsQuery.data ?? []).map((stockLevel) => [
          stockLevel.inventory_item_id,
          stockLevel,
        ]),
      ),
    [stockLevelsQuery.data],
  );
  const theoreticalStockByItemId = useMemo(
    () =>
      new Map(
        (theoreticalStockQuery.data ?? []).map((stockRow) => [
          stockRow.inventory_item_id,
          stockRow,
        ]),
      ),
    [theoreticalStockQuery.data],
  );
  const visibleIngredients = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    const filtered = ingredients.filter((ingredient) =>
      normalizedSearch.length === 0
        ? true
        : ingredient.name.toLowerCase().includes(normalizedSearch),
    );
    return [...filtered].sort((a, b) => {
      if (sort === "cost") {
        return toNumber(b.default_unit_cost) - toNumber(a.default_unit_cost);
      }
      if (sort === "stock") {
        return toNumber(a.estimated_stock_quantity) - toNumber(b.estimated_stock_quantity);
      }
      if (sort === "usage") {
        return b.used_by_product_count - a.used_by_product_count;
      }
      return a.name.localeCompare(b.name, "hu");
    });
  }, [ingredients, search, sort]);

  const saveMutation = useMutation({
    mutationFn: (payload: CatalogIngredientPayload & { id?: string }) => {
      if (payload.id) {
        const { id, business_unit_id: _businessUnitId, ...body } = payload;
        return updateCatalogIngredient(id, body);
      }
      return createCatalogIngredient(payload);
    },
    onSuccess: (ingredient) => {
      setExpandedIngredientId(ingredient.id);
      setIsCreating(false);
      setForm(buildIngredientForm(ingredient));
      void queryClient.invalidateQueries({ queryKey: ["catalog-ingredients", selectedBusinessUnitId] });
      void queryClient.invalidateQueries({ queryKey: ["catalog-products", selectedBusinessUnitId] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
  const deleteMutation = useMutation({
    mutationFn: deleteCatalogIngredient,
    onSuccess: () => {
      setExpandedIngredientId(null);
      setIsCreating(false);
      setForm(buildIngredientForm());
      void queryClient.invalidateQueries({ queryKey: ["catalog-ingredients", selectedBusinessUnitId] });
      void queryClient.invalidateQueries({ queryKey: ["catalog-products", selectedBusinessUnitId] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
  const createMovementMutation = useMutation({
    mutationFn: (payload: InventoryMovementCreatePayload) => createInventoryMovement(payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["catalog-ingredient-movements"] }),
        queryClient.invalidateQueries({ queryKey: ["catalog-stock-levels"] }),
        queryClient.invalidateQueries({ queryKey: ["catalog-theoretical-stock"] }),
        queryClient.invalidateQueries({ queryKey: ["inventory-movements"] }),
        queryClient.invalidateQueries({ queryKey: ["inventory-stock-levels"] }),
        queryClient.invalidateQueries({ queryKey: ["inventory-theoretical-stock"] }),
        queryClient.invalidateQueries({ queryKey: ["inventory-overview-stock-levels"] }),
      ]);
    },
  });

  function startCreate() {
    setForm(buildIngredientForm(undefined, units[0]?.id ?? ""));
    setIsCreating(true);
    setExpandedIngredientId(null);
  }

  useEffect(() => {
    setMovementForm(INITIAL_MOVEMENT_FORM);
    setMovementMessage("");
    setMovementErrorMessage("");
  }, [expandedIngredientId]);

  useEffect(() => {
    setControls(
      <CatalogIngredientsHeaderControls
        businessUnits={businessUnits}
        selectedBusinessUnitId={selectedBusinessUnitId}
        setSelectedBusinessUnitId={(value) => {
          setSelectedBusinessUnitId(value);
          setExpandedIngredientId(null);
          setIsCreating(false);
        }}
        search={search}
        setSearch={setSearch}
        sort={sort}
        setSort={setSort}
        startCreate={startCreate}
      />,
    );

    return () => setControls(null);
  }, [businessUnits, search, selectedBusinessUnitId, setControls, sort]);

  function startEdit(ingredient: CatalogIngredient) {
    setForm(buildIngredientForm(ingredient));
    setIsCreating(false);
    setExpandedIngredientId(ingredient.id);
  }

  function submitIngredientForm(event: FormEvent) {
    event.preventDefault();
    const payload: CatalogIngredientPayload & { id?: string } = {
      id: form.id,
      business_unit_id: form.id ? undefined : selectedBusinessUnitId,
      name: form.name,
      item_type: form.item_type,
      uom_id: form.uom_id,
      default_vat_rate_id: compactNullable(form.default_vat_rate_id),
      track_stock: form.track_stock,
      default_unit_cost: compactNullable(form.default_unit_cost),
      estimated_stock_quantity: compactNullable(form.estimated_stock_quantity),
      is_active: form.is_active,
    };
    saveMutation.mutate(payload);
  }

  function archiveIngredient(ingredient: CatalogIngredient) {
    if (!window.confirm(`Archiválod ezt az alapanyagot: ${ingredient.name}?`)) {
      return;
    }
    deleteMutation.mutate(ingredient.id);
  }

  async function createMovementForIngredient(ingredient: CatalogIngredient) {
    setMovementMessage("");
    setMovementErrorMessage("");

    if (!selectedBusinessUnitId) {
      setMovementErrorMessage("Készletmozgás rögzítéséhez válassz vállalkozást.");
      return;
    }

    if (!movementForm.quantity.trim()) {
      setMovementErrorMessage("Add meg a mozgás mennyiségét.");
      return;
    }

    if (movementForm.movement_type === "purchase" && !movementForm.unit_cost.trim()) {
      setMovementErrorMessage("Beszerzésnél az egységköltség megadása szükséges.");
      return;
    }

    const payload: InventoryMovementCreatePayload = {
      business_unit_id: selectedBusinessUnitId,
      inventory_item_id: ingredient.id,
      movement_type: movementForm.movement_type,
      quantity: movementForm.quantity.trim(),
      uom_id: ingredient.uom_id,
      note: movementForm.note.trim() || undefined,
    };

    if (movementForm.movement_type === "purchase") {
      payload.unit_cost = movementForm.unit_cost.trim();
    } else if (movementForm.unit_cost.trim()) {
      payload.unit_cost = movementForm.unit_cost.trim();
    }

    try {
      await createMovementMutation.mutateAsync(payload);
      setMovementMessage("A készletmozgás rögzítve.");
      setMovementForm(INITIAL_MOVEMENT_FORM);
    } catch (error) {
      setMovementErrorMessage(
        error instanceof Error ? error.message : "Nem sikerült rögzíteni a készletmozgást.",
      );
    }
  }

  const formPanel = isCreating || form.id ? (
    <Card
      className="catalog-editor-card"
      eyebrow={isCreating ? "Új alapanyag" : "Alapanyag szerkesztése"}
      title={isCreating ? "Alapanyag létrehozása" : form.name}
      subtitle="Beszerzési költség, becsült készlet és készletkövetés karbantartása"
    >
      <form className="catalog-edit-form" onSubmit={submitIngredientForm}>
        <div className="form-grid">
          <label className="field">
            <span>Név</span>
            <input className="field-input" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
          </label>
          <label className="field">
            <span>Típus</span>
            <select className="field-input" value={form.item_type} onChange={(event) => setForm({ ...form, item_type: event.target.value })} required>
              <option value="raw_material">Alapanyag</option>
              <option value="packaging">Csomagolóanyag</option>
              <option value="semi_finished">Félkész termék</option>
              <option value="finished_good">Késztermék</option>
            </select>
          </label>
          <label className="field">
            <span>Egység</span>
            <select className="field-input" value={form.uom_id} onChange={(event) => setForm({ ...form, uom_id: event.target.value })} required>
              {units.map((unit) => (
                <option key={unit.id} value={unit.id}>
                  {unit.name} ({unit.symbol ?? unit.code})
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Egységköltség</span>
            <input className="field-input" type="number" min="0" step="0.01" value={form.default_unit_cost} onChange={(event) => setForm({ ...form, default_unit_cost: event.target.value })} />
          </label>
          <label className="field">
            <span>ÁFA kulcs</span>
            <select className="field-input" value={form.default_vat_rate_id} onChange={(event) => setForm({ ...form, default_vat_rate_id: event.target.value })}>
              <option value="">Nincs beállítva</option>
              {vatRates.map((vatRate) => (
                <option key={vatRate.id} value={vatRate.id}>
                  {vatRate.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Becsült készlet</span>
            <input className="field-input" type="number" min="0" step="0.001" value={form.estimated_stock_quantity} onChange={(event) => setForm({ ...form, estimated_stock_quantity: event.target.value })} />
          </label>
          <label className="checkbox-field">
            <input type="checkbox" checked={form.track_stock} onChange={(event) => setForm({ ...form, track_stock: event.target.checked })} />
            <span>Készletkövetés</span>
          </label>
          <label className="checkbox-field">
            <input type="checkbox" checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} />
            <span>Aktív</span>
          </label>
        </div>
        {saveMutation.error ? <p className="error-message">{saveMutation.error.message}</p> : null}
        <div className="catalog-editor-actions">
          <Button type="submit">{saveMutation.isPending ? "Mentés..." : "Mentés"}</Button>
          <Button type="button" variant="secondary" onClick={() => {
            setIsCreating(false);
            setForm(buildIngredientForm());
          }}>
            Mégsem
          </Button>
        </div>
      </form>
    </Card>
  ) : null;

  return (
    <section className="page-section catalog-page">
      <div className="finance-summary-grid">
        <article className="finance-summary-card">
          <span>Alapanyagok</span>
          <strong>{visibleIngredients.length}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Készletkövetés</span>
          <strong>{ingredients.filter((ingredient) => ingredient.track_stock).length}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Alacsony készlet</span>
          <strong>
            {
              visibleIngredients.filter(
                (ingredient) => toNumber(ingredient.estimated_stock_quantity) <= 0,
              ).length
            }
          </strong>
        </article>
        <article className="finance-summary-card">
          <span>Koltseg hiany</span>
          <strong>{visibleIngredients.filter((ingredient) => !ingredient.default_unit_cost).length}</strong>
        </article>
      </div>
      {formPanel}
      {ingredientsQuery.isLoading ? <p className="info-message">Alapanyagok betöltése...</p> : null}
      {stockLevelsQuery.isLoading ? <p className="info-message">Készletszintek betöltése...</p> : null}
      {theoreticalStockQuery.isLoading ? <p className="info-message">Becsült készlet eltérések betöltése...</p> : null}
      {ingredientsQuery.error ? <p className="error-message">{ingredientsQuery.error.message}</p> : null}

      <div className="catalog-card-grid">
        {visibleIngredients.map((ingredient) => {
          const stockQuantity = toNumber(ingredient.estimated_stock_quantity);
          const stockLevel = stockLevelByItemId.get(ingredient.id);
          const theoreticalStock = theoreticalStockByItemId.get(ingredient.id);
          const expanded = expandedIngredientId === ingredient.id;
          const unitLabel = ingredient.uom_symbol ?? ingredient.uom_code ?? "";
          const health = getIngredientHealth({
            trackStock: ingredient.track_stock,
            estimatedStockQuantity: ingredient.estimated_stock_quantity,
            actualQuantity: stockLevel?.current_quantity,
            varianceQuantity: theoreticalStock?.variance_quantity,
          });
          const costHealth = getIngredientCostHealth(ingredient);
          return (
            <Card
              key={ingredient.id}
              as="article"
              hoverable
              className={
                [
                  "catalog-card",
                  stockQuantity <= 0 ? "catalog-card-low-stock" : "",
                  expanded ? "catalog-card-open" : "",
                ]
                  .filter(Boolean)
                  .join(" ")
              }
              eyebrow={formatItemType(ingredient.item_type)}
              title={ingredient.name}
              subtitle={ingredient.track_stock ? "Készletkövetett" : "Nem készletkövetett"}
              count={formatMoney(ingredient.default_unit_cost)}
              onClick={() => setExpandedIngredientId(expanded ? null : ingredient.id)}
            >
              <div className="catalog-card-status-row">
                <span className={health.className}>{health.label}</span>
                <span className={costHealth.className}>{costHealth.label}</span>
              </div>
              <div className="catalog-metrics">
                <span>Becsült készlet <strong>{formatQuantity(ingredient.estimated_stock_quantity, unitLabel)}</strong></span>
                <span>Tényleges készlet <strong>{stockLevel ? formatQuantity(stockLevel.current_quantity, unitLabel) : "-"}</strong></span>
                <span>Eltérés <strong className={toNumber(theoreticalStock?.variance_quantity) < 0 ? "catalog-bad" : "catalog-good"}>{theoreticalStock?.variance_quantity === null || theoreticalStock?.variance_quantity === undefined ? "-" : formatQuantity(theoreticalStock.variance_quantity, unitLabel)}</strong></span>
              </div>
              {expanded ? (
                <div className="catalog-details" onClick={(event) => event.stopPropagation()}>
                  <div className="catalog-health-row">
                    <article className="catalog-health-card">
                      <span>Állapot</span>
                      <strong><span className={health.className}>{health.label}</span></strong>
                    </article>
                    <article className="catalog-health-card">
                      <span>Tényleges</span>
                      <strong>{stockLevel ? formatQuantity(stockLevel.current_quantity, unitLabel) : "-"}</strong>
                    </article>
                    <article className="catalog-health-card">
                      <span>Elméleti</span>
                      <strong>{theoreticalStock?.theoretical_quantity ? formatQuantity(theoreticalStock.theoretical_quantity, unitLabel) : "-"}</strong>
                    </article>
                    <article className="catalog-health-card">
                      <span>Eltérés</span>
                      <strong className={toNumber(theoreticalStock?.variance_quantity) < 0 ? "catalog-bad" : "catalog-good"}>
                        {theoreticalStock?.variance_quantity === null || theoreticalStock?.variance_quantity === undefined ? "-" : formatQuantity(theoreticalStock.variance_quantity, unitLabel)}
                      </strong>
                    </article>
                  </div>
                  <div className="details-grid">
                    <article className="detail-item"><span>Koltseg forrasa</span><strong>{formatCostSourceType(ingredient.default_unit_cost_source_type)}</strong></article>
                    <article className="detail-item"><span>Koltseg frissitve</span><strong>{formatDateTime(ingredient.default_unit_cost_last_seen_at)}</strong></article>
                    <article className="detail-item"><span>Utolsó ismert költség</span><strong>{formatMoney(ingredient.default_unit_cost)}</strong></article>
                    <article className="detail-item"><span>ÁFA kulcs</span><strong>{ingredient.vat_rate_name ?? "Nincs beállítva"}</strong></article>
                    <article className="detail-item"><span>Becslési alap</span><strong>{theoreticalStock ? formatEstimationBasis(theoreticalStock.estimation_basis) : "-"}</strong></article>
                    <article className="detail-item"><span>Utolsó mozgás</span><strong>{formatDateTime(stockLevel?.last_movement_at ?? null)}</strong></article>
                    <article className="detail-item"><span>Utolsó becsült fogyás</span><strong>{formatDateTime(theoreticalStock?.last_estimated_event_at ?? null)}</strong></article>
                    <article className="detail-item"><span>Mozgások száma</span><strong>{stockLevel?.movement_count ?? 0}</strong></article>
                    <article className="detail-item"><span>Recept-használat</span><strong>{ingredient.used_by_product_count} termék</strong></article>
                  </div>
                  <div className="catalog-editor-actions">
                    <Button type="button" variant="secondary" onClick={() => startEdit(ingredient)}>Szerkesztés</Button>
                    <Button type="button" variant="secondary" onClick={() => archiveIngredient(ingredient)} disabled={deleteMutation.isPending}>Archiválás</Button>
                  </div>
                  {stockQuantity <= 0 ? <p className="error-message">A becsült készlet üres vagy nincs beállítva.</p> : null}
                  <div className="catalog-detail-panels">
                    <section className="catalog-detail-panel catalog-detail-panel-wide">
                      <div className="details-panel-header">
                        <h3>Új készletmozgás</h3>
                        <span className="panel-count">{unitLabel}</span>
                      </div>
                      <div className="catalog-movement-form">
                        <label className="field">
                          <span>Típus</span>
                          <select
                            className="field-input"
                            value={movementForm.movement_type}
                            onChange={(event) =>
                              setMovementForm((current) => ({
                                ...current,
                                movement_type: event.target.value as MovementFormState["movement_type"],
                              }))
                            }
                          >
                            <option value="purchase">Beszerzés</option>
                            <option value="adjustment">Korrekció</option>
                            <option value="waste">Selejt</option>
                            <option value="initial_stock">Nyitókészlet</option>
                          </select>
                        </label>

                        <label className="field">
                          <span>Mennyiség</span>
                          <input
                            className="field-input"
                            type="number"
                            min="0"
                            step="0.001"
                            value={movementForm.quantity}
                            onChange={(event) =>
                              setMovementForm((current) => ({
                                ...current,
                                quantity: event.target.value,
                              }))
                            }
                          />
                        </label>

                        <label className="field">
                          <span>Egységköltség</span>
                          <input
                            className="field-input"
                            type="number"
                            min="0"
                            step="0.01"
                            value={movementForm.unit_cost}
                            onChange={(event) =>
                              setMovementForm((current) => ({
                                ...current,
                                unit_cost: event.target.value,
                              }))
                            }
                            placeholder={
                              movementForm.movement_type === "purchase"
                                ? "Beszerzésnél kötelező"
                                : "Opcionális"
                            }
                          />
                        </label>

                        <label className="field catalog-movement-note-field">
                          <span>Megjegyzés</span>
                          <input
                            className="field-input"
                            value={movementForm.note}
                            onChange={(event) =>
                              setMovementForm((current) => ({
                                ...current,
                                note: event.target.value,
                              }))
                            }
                          />
                        </label>

                        <div className="form-actions">
                          <button
                            type="button"
                            className="primary-button"
                            onClick={() => void createMovementForIngredient(ingredient)}
                            disabled={createMovementMutation.isPending}
                          >
                            {createMovementMutation.isPending ? "Rögzítés..." : "Mozgás rögzítése"}
                          </button>
                        </div>
                      </div>
                      {movementMessage ? (
                        <p className="success-message">{movementMessage}</p>
                      ) : null}
                      {movementErrorMessage ? (
                        <p className="error-message">{movementErrorMessage}</p>
                      ) : null}
                    </section>

                    <section className="catalog-detail-panel">
                      <div className="details-panel-header">
                        <h3>Mozgásnapló</h3>
                        <span className="panel-count">{selectedIngredientMovements.length}</span>
                      </div>
                      {selectedIngredientMovementsQuery.isLoading ? (
                        <p className="info-message">Mozgásnapló betöltése...</p>
                      ) : null}
                      {selectedIngredientMovementsQuery.error instanceof Error ? (
                        <p className="error-message">
                          {selectedIngredientMovementsQuery.error.message}
                        </p>
                      ) : null}
                      {!selectedIngredientMovementsQuery.isLoading &&
                      selectedIngredientMovements.length === 0 ? (
                        <p className="empty-message">
                          Nincs készletmozgás ehhez az alapanyaghoz.
                        </p>
                      ) : null}
                      {selectedIngredientMovements.length > 0 ? (
                        <div className="table-wrap catalog-embedded-table">
                          <table className="data-table details-table">
                            <thead>
                              <tr>
                                <th>Időpont</th>
                                <th>Típus</th>
                                <th>Mennyiség</th>
                                <th>Egységköltség</th>
                                <th>Megjegyzés</th>
                              </tr>
                            </thead>
                            <tbody>
                              {selectedIngredientMovements.map((movement) => (
                                <tr key={movement.id}>
                                  <td>{formatDateTime(movement.occurred_at)}</td>
                                  <td>{formatMovementType(movement.movement_type)}</td>
                                  <td>
                                    {formatQuantity(
                                      movement.quantity,
                                      unitLabel,
                                    )}
                                  </td>
                                  <td>{movement.unit_cost ? formatMoney(movement.unit_cost) : "-"}</td>
                                  <td>{movement.note ?? "-"}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : null}
                    </section>

                    <section className="catalog-detail-panel">
                      <div className="details-panel-header">
                        <h3>Fogyási audit</h3>
                        <span className="panel-count">{selectedIngredientAuditRows.length}</span>
                      </div>
                      {selectedIngredientAuditQuery.isLoading ? (
                        <p className="info-message">Fogyási audit betöltése...</p>
                      ) : null}
                      {selectedIngredientAuditQuery.error instanceof Error ? (
                        <p className="error-message">
                          {selectedIngredientAuditQuery.error.message}
                        </p>
                      ) : null}
                      {!selectedIngredientAuditQuery.isLoading &&
                      selectedIngredientAuditRows.length === 0 ? (
                        <p className="empty-message">
                          Nincs POS fogyási audit ehhez az alapanyaghoz.
                        </p>
                      ) : null}
                      {selectedIngredientAuditRows.length > 0 ? (
                        <div className="table-wrap catalog-embedded-table">
                          <table className="data-table details-table">
                            <thead>
                              <tr>
                                <th>Időpont</th>
                                <th>Termék</th>
                                <th>Alap</th>
                                <th>Fogyás</th>
                                <th>Előtte</th>
                                <th>Utána</th>
                                <th>Forrás</th>
                              </tr>
                            </thead>
                            <tbody>
                              {selectedIngredientAuditRows.map((row) => (
                                <tr key={row.id}>
                                  <td>{formatDateTime(row.occurred_at)}</td>
                                  <td>{row.product_name}</td>
                                  <td>{formatEstimationBasis(row.estimation_basis)}</td>
                                  <td>{formatQuantity(row.quantity, row.uom_code)}</td>
                                  <td>{formatQuantity(row.quantity_before, row.uom_code)}</td>
                                  <td>{formatQuantity(row.quantity_after, row.uom_code)}</td>
                                  <td>
                                    {formatSourceType(row.source_type)}
                                    {row.receipt_no ? ` · ${row.receipt_no}` : ""}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : null}
                    </section>
                  </div>
                </div>
              ) : null}
            </Card>
          );
        })}
      </div>
    </section>
  );
}
