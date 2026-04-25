import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "../../../shared/components/ui/Button";
import { Card } from "../../../shared/components/ui/Card";
import { routes } from "../../../shared/constants/routes";
import { listBusinessUnits, listUnitsOfMeasure } from "../../masterData/api/masterDataApi";
import {
  createCatalogIngredient,
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
  track_stock: boolean;
  default_unit_cost: string;
  estimated_stock_quantity: string;
  is_active: boolean;
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

function buildIngredientForm(item?: CatalogIngredient, fallbackUomId = ""): IngredientFormState {
  return {
    id: item?.id,
    name: item?.name ?? "",
    item_type: item?.item_type ?? "raw_material",
    uom_id: item?.uom_id ?? fallbackUomId,
    track_stock: item?.track_stock ?? true,
    default_unit_cost: item?.default_unit_cost ?? "",
    estimated_stock_quantity: item?.estimated_stock_quantity ?? "",
    is_active: item?.is_active ?? true,
  };
}

function compactNullable(value: string) {
  return value.trim() === "" ? null : value.trim();
}

export function CatalogIngredientsPage() {
  const queryClient = useQueryClient();
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<IngredientSort>("abc");
  const [expandedIngredientId, setExpandedIngredientId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [form, setForm] = useState<IngredientFormState>(() => buildIngredientForm());

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

  const ingredients = ingredientsQuery.data ?? [];
  const units = unitsQuery.data ?? [];
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

  function startCreate() {
    setForm(buildIngredientForm(undefined, units[0]?.id ?? ""));
    setIsCreating(true);
    setExpandedIngredientId(null);
  }

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
      track_stock: form.track_stock,
      default_unit_cost: compactNullable(form.default_unit_cost),
      estimated_stock_quantity: compactNullable(form.estimated_stock_quantity),
      is_active: form.is_active,
    };
    saveMutation.mutate(payload);
  }

  const formPanel = isCreating || form.id ? (
    <Card
      className="catalog-editor-card"
      eyebrow={isCreating ? "New ingredient" : "Edit ingredient"}
      title={isCreating ? "Create ingredient" : form.name}
      subtitle="Latest known unit cost and estimated stock can be maintained manually"
    >
      <form className="catalog-edit-form" onSubmit={submitIngredientForm}>
        <div className="form-grid">
          <label className="field">
            <span>Name</span>
            <input className="field-input" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
          </label>
          <label className="field">
            <span>Type</span>
            <input className="field-input" value={form.item_type} onChange={(event) => setForm({ ...form, item_type: event.target.value })} required />
          </label>
          <label className="field">
            <span>Unit</span>
            <select className="field-input" value={form.uom_id} onChange={(event) => setForm({ ...form, uom_id: event.target.value })} required>
              {units.map((unit) => (
                <option key={unit.id} value={unit.id}>
                  {unit.name} ({unit.symbol ?? unit.code})
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Unit cost</span>
            <input className="field-input" type="number" min="0" step="0.01" value={form.default_unit_cost} onChange={(event) => setForm({ ...form, default_unit_cost: event.target.value })} />
          </label>
          <label className="field">
            <span>Estimated stock</span>
            <input className="field-input" type="number" min="0" step="0.001" value={form.estimated_stock_quantity} onChange={(event) => setForm({ ...form, estimated_stock_quantity: event.target.value })} />
          </label>
          <label className="checkbox-field">
            <input type="checkbox" checked={form.track_stock} onChange={(event) => setForm({ ...form, track_stock: event.target.checked })} />
            <span>Track stock</span>
          </label>
          <label className="checkbox-field">
            <input type="checkbox" checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} />
            <span>Active</span>
          </label>
        </div>
        {saveMutation.error ? <p className="error-message">{saveMutation.error.message}</p> : null}
        <div className="catalog-editor-actions">
          <Button type="submit">{saveMutation.isPending ? "Saving..." : "Save"}</Button>
          <Button type="button" variant="secondary" onClick={() => {
            setIsCreating(false);
            setForm(buildIngredientForm());
          }}>
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  ) : null;

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
              setIsCreating(false);
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
          <input className="field-input" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Ingredient name" />
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
        <Button type="button" onClick={startCreate}>New ingredient</Button>
        <Link className="secondary-button" to={routes.catalogProducts}>Products</Link>
      </section>

      {formPanel}
      {ingredientsQuery.isLoading ? <p className="info-message">Loading ingredients...</p> : null}
      {ingredientsQuery.error ? <p className="error-message">{ingredientsQuery.error.message}</p> : null}

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
                <span>Stock <strong>{ingredient.estimated_stock_quantity === null ? "-" : `${formatNumber(ingredient.estimated_stock_quantity)} ${ingredient.uom_symbol ?? ingredient.uom_code ?? ""}`}</strong></span>
                <span>Used by <strong>{ingredient.used_by_product_count}</strong></span>
                <span>Unit <strong>{ingredient.uom_symbol ?? ingredient.uom_code ?? "-"}</strong></span>
              </div>
              {expanded ? (
                <div className="catalog-details" onClick={(event) => event.stopPropagation()}>
                  <div className="details-grid">
                    <article className="detail-item"><span>Latest known cost</span><strong>{formatMoney(ingredient.default_unit_cost)}</strong></article>
                    <article className="detail-item"><span>Estimated stock</span><strong>{ingredient.estimated_stock_quantity === null ? "Not set" : `${formatNumber(ingredient.estimated_stock_quantity)} ${ingredient.uom_symbol ?? ingredient.uom_code ?? ""}`}</strong></article>
                    <article className="detail-item"><span>Recipe coverage</span><strong>{ingredient.used_by_product_count} products</strong></article>
                  </div>
                  <Button type="button" variant="secondary" onClick={() => startEdit(ingredient)}>Edit ingredient</Button>
                  {stockQuantity <= 0 ? <p className="error-message">Estimated stock is empty or not set.</p> : null}
                </div>
              ) : null}
            </Card>
          );
        })}
      </div>
    </section>
  );
}
