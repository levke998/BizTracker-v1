import { Link } from "react-router-dom";

import { routes } from "../../../shared/constants/routes";
import type { Category, Product, UnitOfMeasure, VatRate } from "../../masterData/types/masterData";
import type {
  PosMappingReadiness,
  PosMissingRecipeProduct,
  PosProductAlias,
} from "../../posIngestion/types/posIngestion";
import {
  formatAliasStatus,
  formatDateTime,
  formatMappingReadinessStatus,
  formatMoney,
  toCatalogProductOptionLabel,
  type QuickProductForm,
} from "./importCenterView";

export function PosMappingReadinessPanel({
  readiness,
  isLoading,
}: {
  readiness: PosMappingReadiness | null;
  isLoading: boolean;
}) {
  if (isLoading) {
    return <p className="info-message">Mapping coverage betoltese...</p>;
  }
  if (!readiness) {
    return null;
  }

  const grossCoverage = Math.min(
    100,
    Math.max(0, Number(readiness.gross_revenue_coverage_percent)),
  );

  return (
    <div className={`pos-mapping-readiness status-${readiness.status}`}>
      <div className="pos-mapping-readiness-heading">
        <div>
          <span>Mapping readiness</span>
          <strong>{formatMappingReadinessStatus(readiness.status)}</strong>
        </div>
        <strong>{grossCoverage.toFixed(1)}%</strong>
      </div>
      <div className="vat-readiness-track" aria-hidden="true">
        <span style={{ width: `${grossCoverage}%` }} />
      </div>
      <div className="pos-mapping-readiness-grid">
        <span>
          <strong>
            {readiness.mapped_alias_count}/{readiness.total_alias_count}
          </strong>
          Jovahagyott alias
        </span>
        <span>
          <strong>
            {readiness.mapped_row_count}/{readiness.total_row_count}
          </strong>
          Lefedett POS sor
        </span>
        <span>
          <strong>{formatMoney(readiness.mapped_gross_revenue)}</strong>
          Jovahagyott forgalom
        </span>
        <span>
          <strong>{formatMoney(readiness.automatic_gross_revenue)}</strong>
          Automatikus mapping
        </span>
      </div>
    </div>
  );
}

export function PosQuickProductCreatePanel({
  alias,
  form,
  categories,
  units,
  vatRates,
  isSaving,
  onFormChange,
  onCancel,
  onSubmit,
}: {
  alias: PosProductAlias;
  form: QuickProductForm;
  categories: Category[];
  units: UnitOfMeasure[];
  vatRates: VatRate[];
  isSaving: boolean;
  onFormChange: (next: QuickProductForm) => void;
  onCancel: () => void;
  onSubmit: () => void;
}) {
  return (
    <section className="panel pos-quick-product-panel">
      <div className="panel-header">
        <div>
          <h2>Uj belso termek</h2>
          <p className="panel-description">
            Forras: {alias.source_product_name} · {alias.source_system}
          </p>
        </div>
        <button type="button" className="secondary-button" onClick={onCancel}>
          Megse
        </button>
      </div>

      <div className="form-grid">
        <label className="field">
          <span>Nev</span>
          <input
            className="field-input"
            value={form.name}
            maxLength={200}
            required
            onChange={(event) => onFormChange({ ...form, name: event.target.value })}
          />
        </label>
        <label className="field">
          <span>SKU</span>
          <input
            className="field-input"
            value={form.sku}
            maxLength={64}
            onChange={(event) => onFormChange({ ...form, sku: event.target.value })}
          />
        </label>
        <label className="field">
          <span>Kategoria</span>
          <select
            className="field-input"
            value={form.categoryId}
            onChange={(event) => onFormChange({ ...form, categoryId: event.target.value })}
          >
            <option value="">Nincs kategoria</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Ertekesitesi egyseg</span>
          <select
            className="field-input"
            value={form.salesUomId}
            onChange={(event) => onFormChange({ ...form, salesUomId: event.target.value })}
          >
            <option value="">Nincs egyseg</option>
            {units.map((unit) => (
              <option key={unit.id} value={unit.id}>
                {unit.name} ({unit.symbol ?? unit.code})
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Tipus</span>
          <select
            className="field-input"
            value={form.productType}
            onChange={(event) => onFormChange({ ...form, productType: event.target.value })}
          >
            <option value="finished_good">Kesztermek</option>
            <option value="resale">Tovabbertekesitett termek</option>
            <option value="service">Szolgaltatas</option>
          </select>
        </label>
        <label className="field">
          <span>Eladasi ar</span>
          <input
            className="field-input"
            type="number"
            min="0"
            step="1"
            value={form.salePriceGross}
            onChange={(event) => onFormChange({ ...form, salePriceGross: event.target.value })}
          />
        </label>
        <label className="field">
          <span>AFA kulcs</span>
          <select
            className="field-input"
            value={form.vatRateId}
            onChange={(event) => onFormChange({ ...form, vatRateId: event.target.value })}
          >
            <option value="">Nincs beallitva</option>
            {vatRates.map((vatRate) => (
              <option key={vatRate.id} value={vatRate.id}>
                {vatRate.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="pos-quick-product-actions">
        <small>A mentes letrehozza a katalogustermeket es jovahagyja ezt a POS mappinget.</small>
        <button
          type="button"
          className="primary-button"
          disabled={!form.name.trim() || isSaving}
          onClick={onSubmit}
        >
          {isSaving ? "Letrehozas es mapping..." : "Letrehozas es jovahagyas"}
        </button>
      </div>
    </section>
  );
}

export function PosAliasReviewPanel({
  aliases,
  products,
  businessUnitId,
  isLoading,
  approvingAliasId,
  isBulkApproving,
  statusFilter,
  searchTerm,
  focusedProductId,
  selectedAliasIds,
  selectedProductIds,
  onStatusFilterChange,
  onSearchTermChange,
  onClearProductFocus,
  onStartCreateProduct,
  onSelectProduct,
  onToggleAlias,
  onToggleAllPending,
  onApprove,
  onApproveSelected,
}: {
  aliases: PosProductAlias[];
  products: Product[];
  businessUnitId: string;
  isLoading: boolean;
  approvingAliasId: string;
  isBulkApproving: boolean;
  statusFilter: "all" | "pending" | "mapped";
  searchTerm: string;
  focusedProductId: string;
  selectedAliasIds: string[];
  selectedProductIds: Record<string, string>;
  onStatusFilterChange: (value: "all" | "pending" | "mapped") => void;
  onSearchTermChange: (value: string) => void;
  onClearProductFocus: () => void;
  onStartCreateProduct: (alias: PosProductAlias) => void;
  onSelectProduct: (aliasId: string, productId: string) => void;
  onToggleAlias: (aliasId: string) => void;
  onToggleAllPending: (aliasIds: string[]) => void;
  onApprove: (aliasId: string) => void;
  onApproveSelected: () => void;
}) {
  const pendingAliases = aliases.filter((alias) => alias.status !== "mapped");
  const mappedAliases = aliases.filter((alias) => alias.status === "mapped");
  const productById = new Map(products.map((product) => [product.id, product]));
  const focusedProduct = focusedProductId ? productById.get(focusedProductId) : undefined;
  const selectedAliasIdSet = new Set(selectedAliasIds);
  const normalizedSearch = searchTerm.trim().toLocaleLowerCase("hu-HU");
  const filteredAliases = aliases.filter((alias) => {
    const selectedProductId = selectedProductIds[alias.id] ?? alias.product_id ?? "";
    if (focusedProductId && selectedProductId !== focusedProductId) {
      return false;
    }
    if (statusFilter === "pending" && alias.status === "mapped") {
      return false;
    }
    if (statusFilter === "mapped" && alias.status !== "mapped") {
      return false;
    }
    if (!normalizedSearch) {
      return true;
    }
    return [
      alias.source_product_name,
      alias.source_product_key,
      alias.source_sku ?? "",
      productById.get(selectedProductId)?.name ?? "",
    ].some((value) => value.toLocaleLowerCase("hu-HU").includes(normalizedSearch));
  });
  const visiblePendingAliases = filteredAliases.filter((alias) => alias.status !== "mapped");
  const selectedPendingAliases = visiblePendingAliases.filter((alias) =>
    selectedAliasIdSet.has(alias.id),
  );
  const selectedMissingProductCount = selectedPendingAliases.filter(
    (alias) => !(selectedProductIds[alias.id] ?? alias.product_id),
  ).length;
  const allPendingSelected =
    visiblePendingAliases.length > 0 &&
    visiblePendingAliases.every((alias) => selectedAliasIdSet.has(alias.id));

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>POS termek mapping</h2>
        <span className="panel-count">
          {pendingAliases.length > 0
            ? `${pendingAliases.length} ellenorzendo`
            : `${mappedAliases.length} jovahagyva`}
        </span>
      </div>

      <div className="pos-alias-filter-toolbar">
        <div className="toolbar-group">
          {(["pending", "mapped", "all"] as const).map((filter) => (
            <button
              type="button"
              className={statusFilter === filter ? "filter-chip filter-chip-active" : "filter-chip"}
              key={filter}
              onClick={() => onStatusFilterChange(filter)}
            >
              {filter === "pending"
                ? `Ellenorzendo (${pendingAliases.length})`
                : filter === "mapped"
                  ? `Jovahagyva (${mappedAliases.length})`
                  : `Mind (${aliases.length})`}
            </button>
          ))}
        </div>
        <input
          className="field-input pos-alias-search"
          value={searchTerm}
          placeholder="Kassza- vagy belso termek keresese"
          onChange={(event) => onSearchTermChange(event.target.value)}
        />
      </div>

      {focusedProductId ? (
        <div className="pos-alias-focus-banner">
          <span>
            Katalogus fokusz: <strong>{focusedProduct?.name ?? focusedProductId}</strong>
          </span>
          <button type="button" className="secondary-button" onClick={onClearProductFocus}>
            Fokusz torlese
          </button>
        </div>
      ) : null}

      {visiblePendingAliases.length > 0 ? (
        <div className="pos-alias-bulk-toolbar">
          <label className="checkbox-field">
            <input
              type="checkbox"
              checked={allPendingSelected}
              onChange={() => onToggleAllPending(visiblePendingAliases.map((alias) => alias.id))}
            />
            <span>Minden ellenorzendo alias kijelolese</span>
          </label>
          <div className="pos-alias-bulk-summary">
            <span>{selectedPendingAliases.length} kijelolve</span>
            {selectedMissingProductCount > 0 ? (
              <small>{selectedMissingProductCount} sorhoz meg nincs belso termek</small>
            ) : null}
          </div>
          <button
            type="button"
            className="primary-button"
            disabled={
              selectedPendingAliases.length === 0 ||
              selectedMissingProductCount > 0 ||
              isBulkApproving
            }
            onClick={onApproveSelected}
          >
            {isBulkApproving
              ? "Tomeges mentes..."
              : `${selectedPendingAliases.length} mapping jovahagyasa`}
          </button>
        </div>
      ) : null}

      {isLoading ? <p className="info-message">POS mapping lista betoltese...</p> : null}

      {!isLoading && aliases.length === 0 ? (
        <p className="empty-message">Nincs POS termek alias a kivalasztott vallalkozasnal.</p>
      ) : null}

      {!isLoading && aliases.length > 0 && filteredAliases.length === 0 ? (
        <p className="empty-message">A jelenlegi mapping szurokkel nincs talalat.</p>
      ) : null}

      {filteredAliases.length > 0 ? (
        <div className="table-wrap">
          <table className="data-table details-table">
            <thead>
              <tr>
                <th>Kijeloles</th>
                <th>Kassza termek</th>
                <th>Forras</th>
                <th>Allapot</th>
                <th>Belso termek</th>
                <th>Elofordulas</th>
                <th>Muvelet</th>
              </tr>
            </thead>
            <tbody>
              {filteredAliases.map((alias) => {
                const selectedProductId = selectedProductIds[alias.id] ?? alias.product_id ?? "";
                const selectedProduct = selectedProductId ? productById.get(selectedProductId) : undefined;

                return (
                  <tr
                    key={alias.id}
                    className={selectedAliasIdSet.has(alias.id) ? "selected-row" : undefined}
                  >
                    <td>
                      <input
                        type="checkbox"
                        aria-label={`${alias.source_product_name} kijelolese`}
                        checked={selectedAliasIdSet.has(alias.id)}
                        disabled={alias.status === "mapped" || isBulkApproving}
                        onChange={() => onToggleAlias(alias.id)}
                      />
                    </td>
                    <td>
                      <strong>{alias.source_product_name}</strong>
                      <div className="metric-stack">
                        <span>{alias.source_product_key}</span>
                        {alias.source_sku ? <span>SKU: {alias.source_sku}</span> : null}
                      </div>
                    </td>
                    <td>{alias.source_system}</td>
                    <td>
                      <span className={`status-badge status-${alias.status}`}>
                        {formatAliasStatus(alias.status)}
                      </span>
                    </td>
                    <td>
                      <select
                        className="field-input"
                        value={selectedProductId}
                        disabled={isBulkApproving}
                        onChange={(event) => onSelectProduct(alias.id, event.target.value)}
                      >
                        <option value="">Valassz termeket</option>
                        {products.map((product) => (
                          <option key={product.id} value={product.id}>
                            {toCatalogProductOptionLabel(product)}
                          </option>
                        ))}
                      </select>
                      {selectedProduct ? (
                        <small>
                          {selectedProduct.product_type} ·{" "}
                          <Link
                            to={`${routes.catalogProducts}?${new URLSearchParams({
                              business_unit_id: businessUnitId,
                              product_id: selectedProduct.id,
                              search: selectedProduct.name,
                            }).toString()}`}
                          >
                            Megnyitas a katalogusban
                          </Link>
                        </small>
                      ) : null}
                    </td>
                    <td>
                      <div className="metric-stack">
                        <span>{alias.occurrence_count} sor</span>
                        <span>{alias.last_seen_at ? formatDateTime(alias.last_seen_at) : "-"}</span>
                      </div>
                    </td>
                    <td>
                      <div className="pos-alias-row-actions">
                        {alias.status !== "mapped" && !selectedProductId ? (
                          <button
                            type="button"
                            className="secondary-button"
                            disabled={isBulkApproving}
                            onClick={() => onStartCreateProduct(alias)}
                          >
                            Uj termek
                          </button>
                        ) : null}
                        <button
                          type="button"
                          className="secondary-button"
                          disabled={!selectedProductId || approvingAliasId === alias.id || isBulkApproving}
                          onClick={() => onApprove(alias.id)}
                        >
                          {approvingAliasId === alias.id
                            ? "Mentes..."
                            : alias.status === "mapped"
                              ? "Frissites"
                              : "Jovahagyas"}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

export function PosMissingRecipePanel({
  items,
  isLoading,
}: {
  items: PosMissingRecipeProduct[];
  isLoading: boolean;
}) {
  const sortedItems = [...items].sort((left, right) => {
    if (right.occurrence_count !== left.occurrence_count) {
      return right.occurrence_count - left.occurrence_count;
    }
    return (right.last_seen_at ?? "").localeCompare(left.last_seen_at ?? "");
  });
  const maximumOccurrenceCount = sortedItems[0]?.occurrence_count ?? 0;

  function getPriority(item: PosMissingRecipeProduct) {
    if (maximumOccurrenceCount > 0 && item.occurrence_count >= maximumOccurrenceCount * 0.5) {
      return { label: "Magas", className: "status-pill status-pill-danger" };
    }
    if (maximumOccurrenceCount > 0 && item.occurrence_count >= maximumOccurrenceCount * 0.2) {
      return { label: "Kozepes", className: "status-pill status-pill-warning" };
    }
    return { label: "Normal", className: "status-pill" };
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>POS recept munkalista</h2>
        <span className="panel-count">
          {items.length > 0 ? `${items.length} recept hianyzik` : "Receptfedettseg"}
        </span>
      </div>

      {isLoading ? <p className="info-message">Recept munkalista betoltese...</p> : null}

      {!isLoading && items.length === 0 ? (
        <p className="empty-message">
          Nincs POS-bol erkezett aktiv termek recept hiany jelzessel.
        </p>
      ) : null}

      {items.length > 0 ? (
        <div className="table-wrap">
          <table className="data-table details-table">
            <thead>
              <tr>
                <th>Termek</th>
                <th>Kategoria</th>
                <th>Aktualis ar</th>
                <th>POS forras</th>
                <th>Eladasi jelzes</th>
                <th>Prioritas</th>
                <th>Utoljara latva</th>
                <th>Muvelet</th>
              </tr>
            </thead>
            <tbody>
              {sortedItems.map((item) => {
                const priority = getPriority(item);
                return (
                  <tr key={item.product_id}>
                    <td>
                      <strong>{item.product_name}</strong>
                      <div className="metric-stack">
                        <span>{item.product_type}</span>
                        {item.latest_source_product_name &&
                        item.latest_source_product_name !== item.product_name ? (
                          <span>POS nev: {item.latest_source_product_name}</span>
                        ) : null}
                      </div>
                    </td>
                    <td>{item.category_name ?? "-"}</td>
                    <td>
                      <div className="metric-stack">
                        <span>{formatMoney(item.sale_price_gross)}</span>
                        <span>{item.sale_price_source ?? "-"}</span>
                      </div>
                    </td>
                    <td>
                      <div className="metric-stack">
                        <span>{item.latest_source_system ?? "-"}</span>
                        <span>{item.alias_count} alias</span>
                      </div>
                    </td>
                    <td>{item.occurrence_count} sor</td>
                    <td>
                      <span className={priority.className}>{priority.label}</span>
                    </td>
                    <td>{item.last_seen_at ? formatDateTime(item.last_seen_at) : "-"}</td>
                    <td>
                      <Link
                        className="secondary-button"
                        to={`${routes.productionRecipes}?${new URLSearchParams({
                          business_unit_id: item.business_unit_id,
                          product_id: item.product_id,
                          search: item.product_name,
                          edit: "1",
                          from: "imports",
                        }).toString()}`}
                      >
                        Recept letrehozasa
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
