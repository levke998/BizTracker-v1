import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { Card } from "../../../shared/components/ui/Card";
import { routes } from "../../../shared/constants/routes";
import { listBusinessUnits } from "../../masterData/api/masterDataApi";
import { listCatalogIngredients } from "../api/catalogApi";

type IngredientSort = "abc" | "cost" | "stock" | "usage";

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

export function CatalogIngredientsPage() {
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<IngredientSort>("abc");
  const [expandedIngredientId, setExpandedIngredientId] = useState<string | null>(null);

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

  const ingredients = ingredientsQuery.data ?? [];
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

  return (
    <section className="page-section catalog-page">
      <section className="panel catalog-toolbar">
        <label className="field">
          <span>Business unit</span>
          <select
            className="field-input"
            value={selectedBusinessUnitId}
            onChange={(event) => {
              setSelectedBusinessUnitId(event.target.value);
              setExpandedIngredientId(null);
            }}
          >
            {businessUnits.map((businessUnit) => (
              <option key={businessUnit.id} value={businessUnit.id}>
                {businessUnit.name}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Search</span>
          <input
            className="field-input"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Ingredient name"
          />
        </label>
        <label className="field">
          <span>Sort</span>
          <select className="field-input" value={sort} onChange={(event) => setSort(event.target.value as IngredientSort)}>
            <option value="abc">ABC</option>
            <option value="cost">Purchase cost</option>
            <option value="stock">Estimated stock</option>
            <option value="usage">Recipe usage</option>
          </select>
        </label>
        <Link className="secondary-button" to={routes.catalogProducts}>
          Products
        </Link>
      </section>

      {ingredientsQuery.isLoading ? <p className="info-message">Loading ingredients...</p> : null}
      {ingredientsQuery.error ? (
        <p className="error-message">{ingredientsQuery.error.message}</p>
      ) : null}

      <div className="catalog-card-grid">
        {visibleIngredients.map((ingredient) => {
          const stockQuantity = toNumber(ingredient.estimated_stock_quantity);
          const expanded = expandedIngredientId === ingredient.id;
          return (
            <Card
              key={ingredient.id}
              as="article"
              hoverable
              className={
                stockQuantity <= 0
                  ? "catalog-card catalog-card-low-stock"
                  : expanded
                    ? "catalog-card catalog-card-open"
                    : "catalog-card"
              }
              eyebrow={ingredient.item_type}
              title={ingredient.name}
              subtitle={ingredient.track_stock ? "Stock tracked" : "Stock not tracked"}
              count={formatMoney(ingredient.default_unit_cost)}
              onClick={() => setExpandedIngredientId(expanded ? null : ingredient.id)}
            >
              <div className="catalog-metrics">
                <span>
                  Stock{" "}
                  <strong>
                    {ingredient.estimated_stock_quantity === null
                      ? "-"
                      : `${formatNumber(ingredient.estimated_stock_quantity)} ${ingredient.uom_symbol ?? ingredient.uom_code ?? ""}`}
                  </strong>
                </span>
                <span>
                  Used by <strong>{ingredient.used_by_product_count}</strong>
                </span>
                <span>
                  Unit <strong>{ingredient.uom_symbol ?? ingredient.uom_code ?? "-"}</strong>
                </span>
              </div>
              {expanded ? (
                <div className="catalog-details">
                  <div className="details-grid">
                    <article className="detail-item">
                      <span>Latest known cost</span>
                      <strong>{formatMoney(ingredient.default_unit_cost)}</strong>
                    </article>
                    <article className="detail-item">
                      <span>Estimated stock</span>
                      <strong>
                        {ingredient.estimated_stock_quantity === null
                          ? "Not set"
                          : `${formatNumber(ingredient.estimated_stock_quantity)} ${ingredient.uom_symbol ?? ingredient.uom_code ?? ""}`}
                      </strong>
                    </article>
                    <article className="detail-item">
                      <span>Recipe coverage</span>
                      <strong>{ingredient.used_by_product_count} products</strong>
                    </article>
                  </div>
                  {stockQuantity <= 0 ? (
                    <p className="error-message">Estimated stock is empty or not set.</p>
                  ) : null}
                </div>
              ) : null}
            </Card>
          );
        })}
      </div>
    </section>
  );
}
