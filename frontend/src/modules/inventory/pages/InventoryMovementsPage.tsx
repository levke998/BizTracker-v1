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

function formatMovementType(value: string) {
  const labels: Record<string, string> = {
    purchase: "Beszerzés",
    adjustment: "Korrekció",
    waste: "Selejt",
    initial_stock: "Nyitókészlet",
  };

  return labels[value] ?? value;
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
      setActionErrorMessage("Válassz vállalkozást a készletmozgás rögzítése előtt.");
      return;
    }

    if (!selectedInventoryItem) {
      setActionMessage("");
      setActionErrorMessage("Válassz készletelemet a mozgás rögzítése előtt.");
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
      setActionErrorMessage("Beszerzési mozgásnál kötelező az egységköltség.");
      return;
    }

    try {
      await createMovement(payload);
      setActionMessage(
        `"${selectedInventoryItem.name}" készletmozgása rögzítve.`
      );
      setCreateForm((current) => ({
        ...INITIAL_FORM_STATE,
        inventory_item_id: inventoryItems[0]?.id ?? current.inventory_item_id,
      }));
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : "Nem sikerült rögzíteni a készletmozgást."
      );
    }
  };

  return (
    <section className="page-section">
      <div className="panel">
        <div className="panel-header">
          <h2>Készletmozgások</h2>
          <span className="panel-count">{movements.length}</span>
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
            <span>Mozgástípus</span>
            <select
              value={selectedMovementType}
              onChange={(event) => setSelectedMovementType(event.target.value)}
              className="field-input"
            >
              <option value="">Minden mozgástípus</option>
              <option value="purchase">Beszerzés</option>
              <option value="adjustment">Korrekció</option>
              <option value="waste">Selejt</option>
              <option value="initial_stock">Nyitókészlet</option>
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

        {actionMessage ? <p className="success-message">{actionMessage}</p> : null}
        {actionErrorMessage ? <p className="error-message">{actionErrorMessage}</p> : null}
        {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
        {isLoading ? <p className="info-message">Készletmozgások betöltése...</p> : null}
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Új készletmozgás</h2>
          <span className="panel-count">Új</span>
        </div>

        <div className="form-grid inventory-movement-create-grid">
          <label className="field">
            <span>Készletelem</span>
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
            <span>Mozgástípus</span>
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
              <option value="purchase">Beszerzés</option>
              <option value="adjustment">Korrekció</option>
              <option value="waste">Selejt</option>
              <option value="initial_stock">Nyitókészlet</option>
            </select>
          </label>

          <label className="field">
            <span>Mennyiség</span>
            <input
              value={createForm.quantity}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, quantity: event.target.value }))
              }
              className="field-input"
              placeholder="pl. 12.500"
            />
          </label>

          <label className="field">
            <span>Egységköltség {requiresUnitCost ? "(kötelező)" : "(opcionális)"}</span>
            <input
              value={createForm.unit_cost}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, unit_cost: event.target.value }))
              }
              className="field-input"
              placeholder="pl. 435.50"
            />
          </label>

          <label className="field">
            <span>Időpont</span>
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
            <span>Egység</span>
            <div className="field-input field-readonly">
              {selectedInventoryItem?.uom_id ?? "-"}
            </div>
          </label>

          <label className="field inventory-movement-note-field">
            <span>Megjegyzés</span>
            <input
              value={createForm.note}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, note: event.target.value }))
              }
              className="field-input"
              placeholder="Opcionális megjegyzés"
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
            Mozgás rögzítése
          </button>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Mozgásnapló</h2>
          <span className="panel-count">{movements.length}</span>
        </div>

        {!isLoading && movements.length === 0 ? (
          <p className="empty-message">
            Nincs készletmozgás a kiválasztott szűrőkkel.
          </p>
        ) : null}

        {movements.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Időpont</th>
                  <th>Mozgástípus</th>
                  <th>Mennyiség</th>
                  <th>Egységköltség</th>
                  <th>Tétel azonosító</th>
                  <th>Egység azonosító</th>
                  <th>Megjegyzés</th>
                  <th>Létrehozva</th>
                </tr>
              </thead>
              <tbody>
                {movements.map((movement) => (
                  <tr key={movement.id}>
                    <td>{formatDateTime(movement.occurred_at)}</td>
                    <td>{formatMovementType(movement.movement_type)}</td>
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
