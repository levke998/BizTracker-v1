import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useEstimatedConsumptionAudit } from "../hooks/useEstimatedConsumptionAudit";
import { useTheoreticalStock } from "../hooks/useTheoreticalStock";
import {
  getInventoryVariancePeriodComparison,
  getInventoryVarianceThreshold,
  listInventoryVarianceItemSummary,
  listInventoryVarianceReasonSummary,
  listInventoryVarianceTrend,
  registerPhysicalStockCount,
  updateInventoryVarianceThreshold,
} from "../api/inventoryApi";

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

function formatQuantity(value: string | null) {
  return value ?? "Nincs beállítva";
}

function formatMoney(value: string | null) {
  if (value === null) {
    return "-";
  }
  return new Intl.NumberFormat("hu-HU", {
    style: "currency",
    currency: "HUF",
    maximumFractionDigits: 0,
  }).format(Number(value));
}

function formatItemType(value: string) {
  const labels: Record<string, string> = {
    raw_material: "Alapanyag",
    packaging: "Csomagolóanyag",
    finished_good: "Késztermék",
  };

  return labels[value] ?? value;
}

function formatEstimationBasis(value: string) {
  const labels: Record<string, string> = {
    not_configured: "Nincs beállítva",
    recipe: "Recept alapján",
    recipe_or_direct_pos: "Recept/POS alapján",
    manual: "Kézi beállítás",
    pos_sale: "POS eladás alapján",
  };

  return labels[value] ?? value;
}

function formatBoolean(value: boolean) {
  return value ? "Igen" : "Nem";
}

function getVarianceStatusLabel(value: string) {
  const labels: Record<string, string> = {
    ok: "Rendben",
    missing_theoretical_stock: "Nincs teoretikus készlet",
    missing_cost: "Hiányzó beszerzési ár",
    shortage_risk: "Hiány / selejt gyanú",
    surplus_or_unreviewed: "Többlet / kimaradt fogyás",
  };
  return labels[value] ?? value;
}

function getVarianceStatusClass(value: string) {
  if (value === "ok") {
    return "status-pill status-pill-success";
  }
  if (value === "shortage_risk" || value === "missing_cost") {
    return "status-pill status-pill-danger";
  }
  return "status-pill status-pill-warning";
}

const STOCK_COUNT_REASONS = [
  { value: "physical_count", label: "Fizikai szamolas" },
  { value: "waste", label: "Selejt" },
  { value: "breakage", label: "Tores / kiborulas" },
  { value: "spoilage", label: "Romlas" },
  { value: "theft_suspected", label: "Lopas gyanu" },
  { value: "recipe_error", label: "Hibas recept" },
  { value: "mapping_error", label: "Hibas mapping" },
  { value: "missing_purchase_invoice", label: "Kimaradt beszerzes" },
  { value: "other", label: "Egyeb" },
];

function formatReasonLabel(value: string) {
  return STOCK_COUNT_REASONS.find((reason) => reason.value === value)?.label ?? value;
}

function formatAnomalyStatus(value: string) {
  const labels: Record<string, string> = {
    normal: "Rendben",
    watch: "Figyelendo",
    repeating_loss: "Ismetlodo veszteseg",
    high_loss: "Magas veszteseg",
    missing_cost: "Hianyzo ar",
    surplus_review: "Tobblet ellenorzes",
  };
  return labels[value] ?? value;
}

function getAnomalyStatusClass(value: string) {
  if (value === "normal") {
    return "status-pill status-pill-success";
  }
  if (value === "high_loss" || value === "missing_cost") {
    return "status-pill status-pill-danger";
  }
  return "status-pill status-pill-warning";
}

function formatDecisionStatus(value: string) {
  const labels: Record<string, string> = {
    stable: "Stabil",
    improving: "Javulo",
    watch: "Figyelendo",
    worsening: "Romlik",
    critical: "Kritikus",
    missing_cost: "Hianyzo ar",
  };
  return labels[value] ?? value;
}

function getDecisionStatusClass(value: string) {
  if (value === "stable" || value === "improving") {
    return "status-pill status-pill-success";
  }
  if (value === "critical" || value === "missing_cost") {
    return "status-pill status-pill-danger";
  }
  return "status-pill status-pill-warning";
}

export function TheoreticalStockPage() {
  const queryClient = useQueryClient();
  const [selectedInventoryItemId, setSelectedInventoryItemId] = useState("");
  const [countedQuantity, setCountedQuantity] = useState("");
  const [countReason, setCountReason] = useState("physical_count");
  const [countNote, setCountNote] = useState("");
  const [countMessage, setCountMessage] = useState("");
  const [countErrorMessage, setCountErrorMessage] = useState("");
  const [highLossThreshold, setHighLossThreshold] = useState("");
  const [worseningThreshold, setWorseningThreshold] = useState("");
  const [thresholdMessage, setThresholdMessage] = useState("");
  const [thresholdErrorMessage, setThresholdErrorMessage] = useState("");
  const {
    primaryBusinessUnits,
    technicalBusinessUnits,
    stockRows,
    selectedBusinessUnitId,
    setSelectedBusinessUnitId,
    selectedItemType,
    setSelectedItemType,
    limit,
    setLimit,
    isLoading,
    errorMessage,
  } = useTheoreticalStock();
  const selectedStockRow = stockRows.find(
    (item) => item.inventory_item_id === selectedInventoryItemId
  );
  const auditQuery = useEstimatedConsumptionAudit({
    business_unit_id: selectedBusinessUnitId,
    inventory_item_id: selectedInventoryItemId,
    limit: 25,
  });
  const auditRows = auditQuery.data ?? [];
  const varianceReasonQuery = useQuery({
    queryKey: [
      "inventory-variance-reasons",
      selectedBusinessUnitId,
      selectedInventoryItemId,
    ],
    queryFn: () =>
      listInventoryVarianceReasonSummary({
        business_unit_id: selectedBusinessUnitId || undefined,
        inventory_item_id: selectedInventoryItemId || undefined,
        limit: 20,
      }),
  });
  const varianceReasonRows = varianceReasonQuery.data ?? [];
  const varianceTrendQuery = useQuery({
    queryKey: [
      "inventory-variance-trend",
      selectedBusinessUnitId,
      selectedInventoryItemId,
    ],
    queryFn: () =>
      listInventoryVarianceTrend({
        business_unit_id: selectedBusinessUnitId || undefined,
        inventory_item_id: selectedInventoryItemId || undefined,
        days: 30,
      }),
  });
  const varianceTrendRows = varianceTrendQuery.data ?? [];
  const variancePeriodComparisonQuery = useQuery({
    queryKey: [
      "inventory-variance-period-comparison",
      selectedBusinessUnitId,
      selectedInventoryItemId,
    ],
    queryFn: () =>
      getInventoryVariancePeriodComparison({
        business_unit_id: selectedBusinessUnitId || undefined,
        inventory_item_id: selectedInventoryItemId || undefined,
        days: 30,
      }),
  });
  const variancePeriodComparison = variancePeriodComparisonQuery.data ?? null;
  const varianceThresholdQuery = useQuery({
    queryKey: ["inventory-variance-threshold", selectedBusinessUnitId],
    queryFn: () => getInventoryVarianceThreshold(selectedBusinessUnitId),
    enabled: Boolean(selectedBusinessUnitId),
  });
  const varianceThreshold = varianceThresholdQuery.data ?? null;
  const varianceItemQuery = useQuery({
    queryKey: ["inventory-variance-items", selectedBusinessUnitId],
    queryFn: () =>
      listInventoryVarianceItemSummary({
        business_unit_id: selectedBusinessUnitId || undefined,
        limit: 10,
      }),
  });
  const varianceItemRows = varianceItemQuery.data ?? [];
  const totalCorrectionCount = varianceReasonRows.reduce(
    (total, item) => total + item.movement_count,
    0,
  );
  const totalCorrectionQuantity = varianceReasonRows.reduce(
    (total, item) => total + Math.abs(Number(item.net_quantity_delta)),
    0,
  );
  const totalEstimatedShortageValue = varianceTrendRows.reduce(
    (total, item) => total + Number(item.estimated_shortage_value),
    0,
  );
  const shortageRiskCount = stockRows.filter(
    (item) => item.variance_status === "shortage_risk",
  ).length;
  const missingCostCount = stockRows.filter(
    (item) => item.variance_status === "missing_cost",
  ).length;
  const totalTheoreticalStockValue = stockRows.reduce(
    (total, item) => total + Number(item.theoretical_stock_value ?? 0),
    0,
  );
  const countMutation = useMutation({
    mutationFn: registerPhysicalStockCount,
    onSuccess: async (result) => {
      setCountMessage(
        `Fizikai szamolas rogzitve. Eltérés: ${result.adjustment_quantity}.`,
      );
      setCountedQuantity("");
      setCountNote("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["inventory-theoretical-stock"] }),
        queryClient.invalidateQueries({ queryKey: ["inventory-stock-levels"] }),
        queryClient.invalidateQueries({ queryKey: ["inventory-movements"] }),
        queryClient.invalidateQueries({ queryKey: ["inventory-variance-reasons"] }),
        queryClient.invalidateQueries({ queryKey: ["inventory-variance-trend"] }),
        queryClient.invalidateQueries({
          queryKey: ["inventory-variance-period-comparison"],
        }),
        queryClient.invalidateQueries({ queryKey: ["inventory-variance-items"] }),
      ]);
    },
  });
  const thresholdMutation = useMutation({
    mutationFn: updateInventoryVarianceThreshold,
    onSuccess: async () => {
      setThresholdMessage("Anomalia kuszobok mentve.");
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ["inventory-variance-threshold"],
        }),
        queryClient.invalidateQueries({
          queryKey: ["inventory-variance-period-comparison"],
        }),
        queryClient.invalidateQueries({ queryKey: ["inventory-variance-items"] }),
      ]);
    },
  });

  useEffect(() => {
    if (!varianceThreshold) {
      return;
    }
    setHighLossThreshold(varianceThreshold.high_loss_value_threshold);
    setWorseningThreshold(varianceThreshold.worsening_percent_threshold);
    setThresholdMessage("");
    setThresholdErrorMessage("");
  }, [varianceThreshold]);

  function selectStockRow(inventoryItemId: string) {
    setSelectedInventoryItemId(inventoryItemId);
    const row = stockRows.find((item) => item.inventory_item_id === inventoryItemId);
    setCountedQuantity(row?.actual_quantity ?? "");
    setCountReason("physical_count");
    setCountNote("");
    setCountMessage("");
    setCountErrorMessage("");
  }

  async function submitPhysicalStockCount() {
    setCountMessage("");
    setCountErrorMessage("");
    if (!selectedStockRow) {
      setCountErrorMessage("Valassz keszletelemet a fizikai szamolashoz.");
      return;
    }
    if (!countedQuantity.trim()) {
      setCountErrorMessage("Add meg a megszamolt mennyiseget.");
      return;
    }
    try {
      await countMutation.mutateAsync({
        business_unit_id: selectedStockRow.business_unit_id,
        inventory_item_id: selectedStockRow.inventory_item_id,
        counted_quantity: countedQuantity.trim(),
        uom_id: selectedStockRow.uom_id,
        reason_code: countReason,
        note: countNote.trim() || undefined,
      });
    } catch (error) {
      setCountErrorMessage(
        error instanceof Error ? error.message : "Nem sikerult rogzitni a fizikai szamolast.",
      );
    }
  }

  async function submitVarianceThresholds() {
    setThresholdMessage("");
    setThresholdErrorMessage("");
    if (!selectedBusinessUnitId) {
      setThresholdErrorMessage("Valassz vallalkozast a kuszobok mentesehez.");
      return;
    }
    if (!highLossThreshold.trim() || !worseningThreshold.trim()) {
      setThresholdErrorMessage("Add meg mindket anomalia kuszobot.");
      return;
    }
    try {
      await thresholdMutation.mutateAsync({
        business_unit_id: selectedBusinessUnitId,
        high_loss_value_threshold: highLossThreshold.trim(),
        worsening_percent_threshold: worseningThreshold.trim(),
      });
    } catch (error) {
      setThresholdErrorMessage(
        error instanceof Error ? error.message : "Nem sikerult menteni a kuszoboket.",
      );
    }
  }

  return (
    <section className="page-section">
      <div className="finance-summary-grid">
        <article className="finance-summary-card">
          <span>Teoretikus készletérték</span>
          <strong>{formatMoney(String(totalTheoreticalStockValue))}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Hiány gyanú</span>
          <strong>{shortageRiskCount}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Hiányzó ár</span>
          <strong>{missingCostCount}</strong>
        </article>
      </div>

      <div className="panel">
        <div className="panel-header">
          <h2>Becsült készlet</h2>
          <span className="panel-count">{stockRows.length}</span>
        </div>

        <div className="form-grid inventory-filter-grid">
          <label className="field">
            <span>Vállalkozás</span>
            <select
              value={selectedBusinessUnitId}
              onChange={(event) => setSelectedBusinessUnitId(event.target.value)}
              className="field-input"
            >
              <option value="">Válassz vállalkozást</option>
              {primaryBusinessUnits.length > 0 ? (
                <optgroup label="Vállalkozások">
                  {primaryBusinessUnits.map((businessUnit) => (
                    <option key={businessUnit.id} value={businessUnit.id}>
                      {businessUnit.name}
                    </option>
                  ))}
                </optgroup>
              ) : null}
              {technicalBusinessUnits.length > 0 ? (
                <optgroup label="Technikai">
                  {technicalBusinessUnits.map((businessUnit) => (
                    <option key={businessUnit.id} value={businessUnit.id}>
                      {businessUnit.name} ({businessUnit.code})
                    </option>
                  ))}
                </optgroup>
              ) : null}
            </select>
          </label>

          <label className="field">
            <span>Tételtípus</span>
            <select
              value={selectedItemType}
              onChange={(event) => setSelectedItemType(event.target.value)}
              className="field-input"
            >
              <option value="">Minden tételtípus</option>
              <option value="raw_material">Alapanyag</option>
              <option value="packaging">Csomagolóanyag</option>
              <option value="finished_good">Késztermék</option>
            </select>
          </label>

          <label className="field">
            <span>Megjelenített sorok</span>
            <select
              value={String(limit)}
              onChange={(event) => setLimit(Number(event.target.value))}
              className="field-input"
            >
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
              <option value="200">200</option>
            </select>
          </label>
        </div>

        <p className="info-message">
          A teoretikus készlet recept/POS fogyásból számol, az érték pedig mindig a legfrissebb ismert beszerzési árral készül. Az eltérés selejtet, pazarlást, lopást, hibás receptet vagy kimaradt beszerzést jelezhet.
        </p>

        {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
        {isLoading ? <p className="info-message">Becsült készlet betöltése...</p> : null}
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Becsült készlet állapota</h2>
          <span className="panel-count">{stockRows.length}</span>
        </div>

        {!isLoading && stockRows.length === 0 ? (
          <p className="empty-message">
            Nincs becsült készletsor a kiválasztott szűrőkkel.
          </p>
        ) : null}

        {stockRows.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Név</th>
                  <th>Tételtípus</th>
                  <th>Aktuális mennyiség</th>
                  <th>Teoretikus mennyiség</th>
                  <th>Eltérés</th>
                  <th>Aktuális ár</th>
                  <th>Teoretikus érték</th>
                  <th>Jelzés</th>
                  <th>Becslés alapja</th>
                  <th>Utolsó készletmozgás</th>
                  <th>Utolsó becslési esemény</th>
                  <th>Készletkezelt</th>
                  <th>Aktív</th>
                  <th>Napló</th>
                </tr>
              </thead>
              <tbody>
                {stockRows.map((item) => (
                  <tr key={item.inventory_item_id}>
                    <td>{item.name}</td>
                    <td>{formatItemType(item.item_type)}</td>
                    <td>{item.actual_quantity}</td>
                    <td>{formatQuantity(item.theoretical_quantity)}</td>
                    <td>{formatQuantity(item.variance_quantity)}</td>
                    <td>{formatMoney(item.default_unit_cost)}</td>
                    <td>{formatMoney(item.theoretical_stock_value)}</td>
                    <td>
                      <span className={getVarianceStatusClass(item.variance_status)}>
                        {getVarianceStatusLabel(item.variance_status)}
                      </span>
                    </td>
                    <td>{formatEstimationBasis(item.estimation_basis)}</td>
                    <td>{formatDateTime(item.last_actual_movement_at)}</td>
                    <td>{formatDateTime(item.last_estimated_event_at)}</td>
                    <td>{formatBoolean(item.track_stock)}</td>
                    <td>{formatBoolean(item.is_active)}</td>
                    <td>
                      <button
                        className="secondary-button inventory-audit-button"
                        type="button"
                        onClick={() => selectStockRow(item.inventory_item_id)}
                      >
                        Részletek
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Eltérés okok</h2>
          <span className="panel-count">{totalCorrectionCount}</span>
        </div>

        <div className="finance-summary-grid">
          <article className="finance-summary-card">
            <span>Korrekciós esemény</span>
            <strong>{totalCorrectionCount}</strong>
          </article>
          <article className="finance-summary-card">
            <span>Összes érintett mennyiség</span>
            <strong>{totalCorrectionQuantity.toFixed(3)}</strong>
          </article>
          <article className="finance-summary-card">
            <span>Leggyakoribb ok</span>
            <strong>
              {varianceReasonRows[0]
                ? formatReasonLabel(varianceReasonRows[0].reason_code)
                : "-"}
            </strong>
          </article>
        </div>

        <p className="info-message">
          Ezek a fizikai számolásból és készletkorrekcióból származó okok. Ez controlling jelzés: miből keletkezik eltérés a teoretikus készlethez képest.
        </p>

        {varianceReasonQuery.error instanceof Error ? (
          <p className="error-message">{varianceReasonQuery.error.message}</p>
        ) : null}
        {varianceReasonQuery.isLoading ? (
          <p className="info-message">Eltérés okok betöltése...</p>
        ) : null}
        {!varianceReasonQuery.isLoading && varianceReasonRows.length === 0 ? (
          <p className="empty-message">
            Még nincs fizikai számolásból vagy ok-kódos korrekcióból származó eltérés.
          </p>
        ) : null}

        {varianceReasonRows.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Ok</th>
                  <th>Események</th>
                  <th>Összes mennyiség</th>
                  <th>Nettó készlethatás</th>
                  <th>Utolsó előfordulás</th>
                </tr>
              </thead>
              <tbody>
                {varianceReasonRows.map((row) => (
                  <tr key={row.reason_code}>
                    <td>{formatReasonLabel(row.reason_code)}</td>
                    <td>{row.movement_count}</td>
                    <td>{row.total_quantity}</td>
                    <td>{row.net_quantity_delta}</td>
                    <td>{formatDateTime(row.latest_occurred_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Eltérés trend és veszteség</h2>
          <span className="panel-count">{varianceTrendRows.length}</span>
        </div>

        <p className="info-message">
          Az utolsó 30 nap korrekciói napi bontásban, valamint a legnagyobb veszteséget mutató készletelemek.
        </p>

        {variancePeriodComparisonQuery.error instanceof Error ? (
          <p className="error-message">
            {variancePeriodComparisonQuery.error.message}
          </p>
        ) : null}
        {varianceTrendQuery.error instanceof Error ? (
          <p className="error-message">{varianceTrendQuery.error.message}</p>
        ) : null}
        {varianceItemQuery.error instanceof Error ? (
          <p className="error-message">{varianceItemQuery.error.message}</p>
        ) : null}
        {varianceTrendQuery.isLoading || varianceItemQuery.isLoading ? (
          <p className="info-message">Eltérés trend betöltése...</p>
        ) : null}

        {variancePeriodComparison ? (
          <>
            <div className="finance-summary-grid">
              <article className="finance-summary-card">
                <span>Idoszaki jelzes</span>
                <strong>
                  <span
                    className={getDecisionStatusClass(
                      variancePeriodComparison.decision_status,
                    )}
                  >
                    {formatDecisionStatus(variancePeriodComparison.decision_status)}
                  </span>
                </strong>
              </article>
              <article className="finance-summary-card">
                <span>Aktualis 30 nap veszteseg</span>
                <strong>
                  {formatMoney(
                    variancePeriodComparison.current_estimated_shortage_value,
                  )}
                </strong>
              </article>
              <article className="finance-summary-card">
                <span>Elozo 30 nap veszteseg</span>
                <strong>
                  {formatMoney(
                    variancePeriodComparison.previous_estimated_shortage_value,
                  )}
                </strong>
              </article>
              <article className="finance-summary-card">
                <span>Valtozas</span>
                <strong>
                  {formatMoney(
                    variancePeriodComparison.estimated_shortage_value_change,
                  )}
                </strong>
                <small>
                  {variancePeriodComparison.estimated_shortage_value_change_percent
                    ? `${variancePeriodComparison.estimated_shortage_value_change_percent}%`
                    : "nincs elozo bazis"}
                </small>
              </article>
            </div>
            <p className="info-message">
              {variancePeriodComparison.recommendation}
            </p>
          </>
        ) : null}

        <div className="form-grid inventory-filter-grid">
          <label className="field">
            <span>Magas veszteseg kuszob (Ft)</span>
            <input
              className="field-input"
              type="number"
              min="0"
              step="100"
              value={highLossThreshold}
              onChange={(event) => setHighLossThreshold(event.target.value)}
            />
          </label>
          <label className="field">
            <span>Romlas kuszob (%)</span>
            <input
              className="field-input"
              type="number"
              min="0"
              step="1"
              value={worseningThreshold}
              onChange={(event) => setWorseningThreshold(event.target.value)}
            />
          </label>
          <div className="field form-action-field">
            <span>Kuszob forras</span>
            <button
              className="primary-button"
              type="button"
              onClick={submitVarianceThresholds}
              disabled={thresholdMutation.isPending}
            >
              Kuszobok mentese
            </button>
          </div>
        </div>
        <p className="section-note">
          {varianceThreshold?.is_default
            ? "Jelenleg alapertelmezett kuszobok ervenyesek."
            : "Uzletre mentett kuszobok ervenyesek."}
        </p>
        {thresholdMessage ? <p className="info-message">{thresholdMessage}</p> : null}
        {thresholdErrorMessage ? (
          <p className="error-message">{thresholdErrorMessage}</p>
        ) : null}
        {varianceThresholdQuery.error instanceof Error ? (
          <p className="error-message">{varianceThresholdQuery.error.message}</p>
        ) : null}

        <div className="finance-summary-grid">
          <article className="finance-summary-card">
            <span>Trend napok</span>
            <strong>{varianceTrendRows.length}</strong>
          </article>
          <article className="finance-summary-card">
            <span>Top veszteség tétel</span>
            <strong>{varianceItemRows[0]?.name ?? "-"}</strong>
          </article>
          <article className="finance-summary-card">
            <span>Top veszteség mennyiség</span>
            <strong>{varianceItemRows[0]?.shortage_quantity ?? "-"}</strong>
          </article>
          <article className="finance-summary-card">
            <span>Becsült veszteség</span>
            <strong>{formatMoney(String(totalEstimatedShortageValue))}</strong>
          </article>
        </div>

        {varianceTrendRows.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Nap</th>
                  <th>Események</th>
                  <th>Hiány / veszteség</th>
                  <th>Többlet</th>
                  <th>Nettó hatás</th>
                  <th>Becsült veszteség</th>
                  <th>Becsült nettó hatás</th>
                  <th>Hiányzó ár</th>
                </tr>
              </thead>
              <tbody>
                {varianceTrendRows.map((row) => (
                  <tr key={row.bucket_date}>
                    <td>{formatDateTime(row.bucket_date)}</td>
                    <td>{row.movement_count}</td>
                    <td>{row.shortage_quantity}</td>
                    <td>{row.surplus_quantity}</td>
                    <td>{row.net_quantity_delta}</td>
                    <td>{formatMoney(row.estimated_shortage_value)}</td>
                    <td>{formatMoney(row.estimated_net_value_delta)}</td>
                    <td>{row.missing_cost_movement_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {varianceItemRows.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Készletelem</th>
                  <th>Típus</th>
                  <th>Események</th>
                  <th>Hiány / veszteség</th>
                  <th>Többlet</th>
                  <th>Nettó hatás</th>
                  <th>Aktuális ár</th>
                  <th>Becsült veszteség</th>
                  <th>Becsült nettó hatás</th>
                  <th>Jelzés</th>
                  <th>Utolsó előfordulás</th>
                </tr>
              </thead>
              <tbody>
                {varianceItemRows.map((row) => (
                  <tr key={row.inventory_item_id}>
                    <td>{row.name}</td>
                    <td>{formatItemType(row.item_type)}</td>
                    <td>{row.movement_count}</td>
                    <td>{row.shortage_quantity}</td>
                    <td>{row.surplus_quantity}</td>
                    <td>{row.net_quantity_delta}</td>
                    <td>{formatMoney(row.default_unit_cost)}</td>
                    <td>{formatMoney(row.estimated_shortage_value)}</td>
                    <td>{formatMoney(row.estimated_net_value_delta)}</td>
                    <td>
                      <span className={getAnomalyStatusClass(row.anomaly_status)}>
                        {formatAnomalyStatus(row.anomaly_status)}
                      </span>
                    </td>
                    <td>{formatDateTime(row.latest_occurred_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {!varianceTrendQuery.isLoading &&
        !varianceItemQuery.isLoading &&
        varianceTrendRows.length === 0 &&
        varianceItemRows.length === 0 ? (
          <p className="empty-message">
            Még nincs trendhez elegendő ok-kódos készletkorrekció.
          </p>
        ) : null}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Fogyási napló</h2>
          <span className="panel-count">{auditRows.length}</span>
        </div>

        {!selectedStockRow ? (
          <p className="empty-message">Válassz készletelemet a becsült fogyás megtekintéséhez.</p>
        ) : null}

        {selectedStockRow ? (
          <p className="info-message">
            {selectedStockRow.name} becsült készletváltozásai POS eladások alapján.
          </p>
        ) : null}

        {selectedStockRow ? (
          <div className="form-grid inventory-filter-grid">
            <label className="field">
              <span>Megszamolt mennyiseg</span>
              <input
                className="field-input"
                type="number"
                min="0"
                step="0.001"
                value={countedQuantity}
                onChange={(event) => setCountedQuantity(event.target.value)}
              />
            </label>
            <label className="field">
              <span>Eltérés oka</span>
              <select
                className="field-input"
                value={countReason}
                onChange={(event) => setCountReason(event.target.value)}
              >
                {STOCK_COUNT_REASONS.map((reason) => (
                  <option key={reason.value} value={reason.value}>
                    {reason.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Megjegyzes</span>
              <input
                className="field-input"
                value={countNote}
                onChange={(event) => setCountNote(event.target.value)}
              />
            </label>
            <div className="form-actions">
              <button
                type="button"
                className="primary-button"
                onClick={() => void submitPhysicalStockCount()}
                disabled={countMutation.isPending}
              >
                {countMutation.isPending ? "Rogzites..." : "Fizikai szamolas rogzitese"}
              </button>
            </div>
          </div>
        ) : null}

        {countMessage ? <p className="success-message">{countMessage}</p> : null}
        {countErrorMessage ? <p className="error-message">{countErrorMessage}</p> : null}

        {auditQuery.error instanceof Error ? (
          <p className="error-message">{auditQuery.error.message}</p>
        ) : null}
        {auditQuery.isLoading ? (
          <p className="info-message">Fogyási napló betöltése...</p>
        ) : null}

        {selectedStockRow && !auditQuery.isLoading && auditRows.length === 0 ? (
          <p className="empty-message">Nincs becsült fogyási napló ehhez a tételhez.</p>
        ) : null}

        {auditRows.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Időpont</th>
                  <th>Termék</th>
                  <th>Alap</th>
                  <th>Mennyiség</th>
                  <th>Előtte</th>
                  <th>Utána</th>
                  <th>Nyugta</th>
                  <th>Forrás</th>
                </tr>
              </thead>
              <tbody>
                {auditRows.map((row) => (
                  <tr key={row.id}>
                    <td>{formatDateTime(row.occurred_at)}</td>
                    <td>{row.product_name}</td>
                    <td>{formatEstimationBasis(row.estimation_basis)}</td>
                    <td>
                      {row.quantity} {row.uom_code}
                    </td>
                    <td>{row.quantity_before}</td>
                    <td>{row.quantity_after}</td>
                    <td>{row.receipt_no ?? "-"}</td>
                    <td className="mono-cell">{row.source_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </section>
  );
}
