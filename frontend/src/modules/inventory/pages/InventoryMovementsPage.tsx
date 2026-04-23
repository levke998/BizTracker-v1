import { useEffect, useMemo, useState } from "react";

import type { InventoryMovementCreatePayload } from "../types/inventory";
import { useInventoryMovements } from "../hooks/useInventoryMovements";

type MovementFormState = {
  inventory_item_id: string;
  movement_type: "purchase" | "adjustment" | "waste" | "initial_stock";
  quantity: string;
  unit_cost: string;
  note: string;
  occurred_at: string;
};

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

const INITIAL_FORM_STATE: MovementFormState = {
  inventory_item_id: "",
  movement_type: "purchase",
  quantity: "",
  unit_cost: "",
  note: "",
  occurred_at: "",
};

export function InventoryMovementsPage() {
  const {
    primaryBusinessUnits,
    technicalBusinessUnits,
    inventoryItems,
    movements,
    selectedBusinessUnitId,
    setSelectedBusinessUnitId,
    selectedMovementType,
    setSelectedMovementType,
    limit,
    setLimit,
    createMovement,
    isSaving,
    isLoading,
    errorMessage,
  } = useInventoryMovements();

  const [createForm, setCreateForm] = useState<MovementFormState>(INITIAL_FORM_STATE);
  const [actionMessage, setActionMessage] = useState("");
  const [actionErrorMessage, setActionErrorMessage] = useState("");

  useEffect(() => {
    if (!createForm.inventory_item_id && inventoryItems[0]?.id) {
      setCreateForm((current) => ({ ...current, inventory_item_id: inventoryItems[0].id }));
    }
  }, [createForm.inventory_item_id, inventoryItems]);

  useEffect(() => {
    setCreateForm((current) => ({
      ...current,
      inventory_item_id:
        inventoryItems.find((item) => item.id === current.inventory_item_id)?.id ??
        inventoryItems[0]?.id ??
        "",
    }));
  }, [inventoryItems]);

  const selectedInventoryItem = useMemo(
    () =>
      inventoryItems.find((item) => item.id === createForm.inventory_item_id) ?? null,
    [createForm.inventory_item_id, inventoryItems]
  );

  const requiresUnitCost = createForm.movement_type === "purchase";

  const handleCreate = async () => {
    if (!selectedBusinessUnitId) {
      setActionMessage("");
      setActionErrorMessage("Select a business unit before creating a movement.");
      return;
    }

    if (!selectedInventoryItem) {
      setActionMessage("");
      setActionErrorMessage("Select an inventory item before creating a movement.");
      return;
    }

    setActionMessage("");
    setActionErrorMessage("");

    const payload: InventoryMovementCreatePayload = {
      business_unit_id: selectedBusinessUnitId,
      inventory_item_id: selectedInventoryItem.id,
      movement_type: createForm.movement_type,
      quantity: createForm.quantity.trim(),
      uom_id: selectedInventoryItem.uom_id,
      note: createForm.note.trim() || undefined,
      occurred_at: createForm.occurred_at
        ? new Date(createForm.occurred_at).toISOString()
        : undefined,
    };

    if (requiresUnitCost && createForm.unit_cost.trim()) {
      payload.unit_cost = createForm.unit_cost.trim();
    } else if (requiresUnitCost && !createForm.unit_cost.trim()) {
      setActionErrorMessage("Unit cost is required for purchase movements.");
      return;
    }

    try {
      await createMovement(payload);
      setActionMessage(
        `Inventory movement for "${selectedInventoryItem.name}" created successfully.`
      );
      setCreateForm((current) => ({
        ...INITIAL_FORM_STATE,
        inventory_item_id: inventoryItems[0]?.id ?? current.inventory_item_id,
      }));
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : "Failed to create inventory movement."
      );
    }
  };

  return (
    <section className="page-section">
      <div className="panel">
        <div className="panel-header">
          <h2>Inventory Movements</h2>
          <span className="panel-count">{movements.length}</span>
        </div>

        <div className="form-grid inventory-filter-grid">
          <label className="field">
            <span>Business unit</span>
            <select
              value={selectedBusinessUnitId}
              onChange={(event) => setSelectedBusinessUnitId(event.target.value)}
              className="field-input"
            >
              <option value="">Select a business unit</option>
              {primaryBusinessUnits.length > 0 ? (
                <optgroup label="Business units">
                  {primaryBusinessUnits.map((businessUnit) => (
                    <option key={businessUnit.id} value={businessUnit.id}>
                      {businessUnit.name}
                    </option>
                  ))}
                </optgroup>
              ) : null}
              {technicalBusinessUnits.length > 0 ? (
                <optgroup label="Technical">
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
            <span>Movement type</span>
            <select
              value={selectedMovementType}
              onChange={(event) => setSelectedMovementType(event.target.value)}
              className="field-input"
            >
              <option value="">All movement types</option>
              <option value="purchase">purchase</option>
              <option value="adjustment">adjustment</option>
              <option value="waste">waste</option>
              <option value="initial_stock">initial_stock</option>
            </select>
          </label>

          <label className="field">
            <span>Limit</span>
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

        {actionMessage ? <p className="success-message">{actionMessage}</p> : null}
        {actionErrorMessage ? <p className="error-message">{actionErrorMessage}</p> : null}
        {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
        {isLoading ? <p className="info-message">Loading inventory movements...</p> : null}
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Create movement</h2>
          <span className="panel-count">New</span>
        </div>

        <div className="form-grid inventory-movement-create-grid">
          <label className="field">
            <span>Inventory item</span>
            <select
              value={createForm.inventory_item_id}
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  inventory_item_id: event.target.value,
                }))
              }
              className="field-input"
            >
              {inventoryItems.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} ({item.item_type})
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Movement type</span>
            <select
              value={createForm.movement_type}
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  movement_type: event.target.value as MovementFormState["movement_type"],
                }))
              }
              className="field-input"
            >
              <option value="purchase">purchase</option>
              <option value="adjustment">adjustment</option>
              <option value="waste">waste</option>
              <option value="initial_stock">initial_stock</option>
            </select>
          </label>

          <label className="field">
            <span>Quantity</span>
            <input
              value={createForm.quantity}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, quantity: event.target.value }))
              }
              className="field-input"
              placeholder="e.g. 12.500"
            />
          </label>

          <label className="field">
            <span>Unit cost {requiresUnitCost ? "(required)" : "(optional)"}</span>
            <input
              value={createForm.unit_cost}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, unit_cost: event.target.value }))
              }
              className="field-input"
              placeholder="e.g. 435.50"
            />
          </label>

          <label className="field">
            <span>Occurred at</span>
            <input
              type="datetime-local"
              value={createForm.occurred_at}
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  occurred_at: event.target.value,
                }))
              }
              className="field-input"
            />
          </label>

          <label className="field inventory-movement-uom-field">
            <span>UOM</span>
            <div className="field-input field-readonly">
              {selectedInventoryItem?.uom_id ?? "-"}
            </div>
          </label>

          <label className="field inventory-movement-note-field">
            <span>Note</span>
            <input
              value={createForm.note}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, note: event.target.value }))
              }
              className="field-input"
              placeholder="Optional note"
            />
          </label>
        </div>

        <div className="inline-actions">
          <button
            type="button"
            className="primary-button"
            onClick={handleCreate}
            disabled={
              isSaving ||
              !selectedBusinessUnitId ||
              !selectedInventoryItem ||
              !createForm.quantity.trim() ||
              (requiresUnitCost && !createForm.unit_cost.trim())
            }
          >
            Create movement
          </button>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Movement log</h2>
          <span className="panel-count">{movements.length}</span>
        </div>

        {!isLoading && movements.length === 0 ? (
          <p className="empty-message">
            No inventory movements found for the selected filters.
          </p>
        ) : null}

        {movements.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Occurred at</th>
                  <th>Movement type</th>
                  <th>Quantity</th>
                  <th>Unit cost</th>
                  <th>Item ID</th>
                  <th>UOM ID</th>
                  <th>Note</th>
                  <th>Created at</th>
                </tr>
              </thead>
              <tbody>
                {movements.map((movement) => (
                  <tr key={movement.id}>
                    <td>{formatDateTime(movement.occurred_at)}</td>
                    <td>{movement.movement_type}</td>
                    <td>{movement.quantity}</td>
                    <td>{movement.unit_cost ?? "-"}</td>
                    <td>{movement.inventory_item_id}</td>
                    <td>{movement.uom_id}</td>
                    <td>{movement.note ?? "-"}</td>
                    <td>{formatDateTime(movement.created_at)}</td>
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
