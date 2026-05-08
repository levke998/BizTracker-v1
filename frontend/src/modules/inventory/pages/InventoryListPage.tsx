import { useEffect, useMemo, useState } from "react";

import type { UnitOfMeasure } from "../../masterData/types/masterData";
import type {
  InventoryItem,
  InventoryItemCreatePayload,
  InventoryItemUpdatePayload,
} from "../types/inventory";
import { useInventoryItems } from "../hooks/useInventoryItems";

type EditFormState = {
  name: string;
  item_type: string;
  uom_id: string;
  track_stock: boolean;
  is_active: boolean;
};

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("hu-HU", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function createEditFormState(item: InventoryItem): EditFormState {
  return {
    name: item.name,
    item_type: item.item_type,
    uom_id: item.uom_id,
    track_stock: item.track_stock,
    is_active: item.is_active,
  };
}

function getUnitOfMeasureLabel(item: UnitOfMeasure) {
  if (item.symbol) {
    return `${item.name} (${item.code} / ${item.symbol})`;
  }

  return `${item.name} (${item.code})`;
}

function formatItemType(value: string) {
  const labels: Record<string, string> = {
    raw_material: "Alapanyag",
    packaging: "Csomagolóanyag",
    finished_good: "Késztermék",
  };

  return labels[value] ?? value;
}

function formatBoolean(value: boolean) {
  return value ? "Igen" : "Nem";
}

export function InventoryListPage() {
  const {
    primaryBusinessUnits,
    technicalBusinessUnits,
    unitsOfMeasure,
    items,
    selectedBusinessUnitId,
    setSelectedBusinessUnitId,
    selectedItemType,
    setSelectedItemType,
    limit,
    setLimit,
    createItem,
    updateItem,
    archiveItem,
    isSaving,
    isLoading,
    errorMessage,
  } = useInventoryItems();

  const [createForm, setCreateForm] = useState<EditFormState>({
    name: "",
    item_type: "raw_material",
    uom_id: "",
    track_stock: true,
    is_active: true,
  });
  const [editingItemId, setEditingItemId] = useState("");
  const [editForm, setEditForm] = useState<EditFormState | null>(null);
  const [actionMessage, setActionMessage] = useState("");
  const [actionErrorMessage, setActionErrorMessage] = useState("");

  useEffect(() => {
    if (!createForm.uom_id && unitsOfMeasure[0]?.id) {
      setCreateForm((current) => ({ ...current, uom_id: unitsOfMeasure[0].id }));
    }
  }, [createForm.uom_id, unitsOfMeasure]);

  const editingItem = useMemo(
    () => items.find((item) => item.id === editingItemId) ?? null,
    [editingItemId, items]
  );

  useEffect(() => {
    if (!editingItem) {
      return;
    }

    setEditForm(createEditFormState(editingItem));
  }, [editingItem]);

  const startEditing = (item: InventoryItem) => {
    setEditingItemId(item.id);
    setEditForm(createEditFormState(item));
    setActionMessage("");
    setActionErrorMessage("");
  };

  const cancelEditing = () => {
    setEditingItemId("");
    setEditForm(null);
    setActionErrorMessage("");
  };

  const handleSubmit = async () => {
    if (!editingItem || !editForm) {
      return;
    }

    setActionMessage("");
    setActionErrorMessage("");

    const payload: InventoryItemUpdatePayload = {
      name: editForm.name.trim(),
      item_type: editForm.item_type,
      uom_id: editForm.uom_id,
      track_stock: editForm.track_stock,
      is_active: editForm.is_active,
    };

    try {
      await updateItem(editingItem.id, payload);
      setActionMessage(`"${payload.name}" készletelem frissítve.`);
      setEditingItemId("");
      setEditForm(null);
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : "Nem sikerült frissíteni a készletelemet."
      );
    }
  };

  const handleCreate = async () => {
    if (!selectedBusinessUnitId) {
      setActionMessage("");
      setActionErrorMessage("Válassz vállalkozást a készletelem létrehozása előtt.");
      return;
    }

    setActionMessage("");
    setActionErrorMessage("");

    const payload: InventoryItemCreatePayload = {
      business_unit_id: selectedBusinessUnitId,
      name: createForm.name.trim(),
      item_type: createForm.item_type,
      uom_id: createForm.uom_id,
      track_stock: createForm.track_stock,
      is_active: createForm.is_active,
    };

    try {
      await createItem(payload);
      setActionMessage(`"${payload.name}" készletelem létrehozva.`);
      setCreateForm((current) => ({
        ...current,
        name: "",
        item_type: "raw_material",
        track_stock: true,
        is_active: true,
      }));
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : "Nem sikerült létrehozni a készletelemet."
      );
    }
  };

  const handleArchive = async (item: InventoryItem) => {
    if (!window.confirm(`Archiváljuk ezt a készletelemet: "${item.name}"?`)) {
      return;
    }

    setActionMessage("");
    setActionErrorMessage("");

    try {
      await archiveItem(item.id);
      if (editingItemId === item.id) {
        setEditingItemId("");
        setEditForm(null);
      }
      setActionMessage(`"${item.name}" készletelem archiválva.`);
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : "Nem sikerült archiválni a készletelemet."
      );
    }
  };

  return (
    <section className="page-section">
      <div className="panel">
        <div className="panel-header">
          <h2>Készletelemek</h2>
          <span className="panel-count">{items.length}</span>
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

        {actionMessage ? <p className="success-message">{actionMessage}</p> : null}
        {actionErrorMessage ? <p className="error-message">{actionErrorMessage}</p> : null}
        {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
        {isLoading ? <p className="info-message">Készletelemek betöltése...</p> : null}
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Új készletelem</h2>
          <span className="panel-count">Új</span>
        </div>

        <div className="form-grid inventory-edit-grid">
          <label className="field">
            <span>Név</span>
            <input
              value={createForm.name}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, name: event.target.value }))
              }
              className="field-input"
            />
          </label>

          <label className="field">
            <span>Tételtípus</span>
            <select
              value={createForm.item_type}
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  item_type: event.target.value,
                }))
              }
              className="field-input"
            >
              <option value="raw_material">Alapanyag</option>
              <option value="packaging">Csomagolóanyag</option>
              <option value="finished_good">Késztermék</option>
            </select>
          </label>

          <label className="field">
            <span>Mértékegység</span>
            <select
              value={createForm.uom_id}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, uom_id: event.target.value }))
              }
              className="field-input"
            >
              {unitsOfMeasure.map((item) => (
                <option key={item.id} value={item.id}>
                  {getUnitOfMeasureLabel(item)}
                </option>
              ))}
            </select>
          </label>

          <label className="field checkbox-field">
            <span>Készletkezelt</span>
            <input
              type="checkbox"
              checked={createForm.track_stock}
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  track_stock: event.target.checked,
                }))
              }
            />
          </label>

          <label className="field checkbox-field">
            <span>Aktív</span>
            <input
              type="checkbox"
              checked={createForm.is_active}
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  is_active: event.target.checked,
                }))
              }
            />
          </label>
        </div>

        <div className="inline-actions">
          <button
            type="button"
            className="primary-button"
            onClick={handleCreate}
            disabled={isSaving || !selectedBusinessUnitId || !createForm.name.trim() || !createForm.uom_id}
          >
            Készletelem létrehozása
          </button>
        </div>
      </section>

      {editingItem && editForm ? (
        <section className="panel">
          <div className="panel-header">
            <h2>Készletelem szerkesztése</h2>
            <span className="panel-count">1</span>
          </div>

          <div className="form-grid inventory-edit-grid">
            <label className="field">
              <span>Név</span>
              <input
                value={editForm.name}
                onChange={(event) =>
                  setEditForm((current) =>
                    current ? { ...current, name: event.target.value } : current
                  )
                }
                className="field-input"
              />
            </label>

            <label className="field">
              <span>Tételtípus</span>
              <select
                value={editForm.item_type}
                onChange={(event) =>
                  setEditForm((current) =>
                    current ? { ...current, item_type: event.target.value } : current
                  )
                }
                className="field-input"
              >
                <option value="raw_material">Alapanyag</option>
                <option value="packaging">Csomagolóanyag</option>
                <option value="finished_good">Késztermék</option>
              </select>
            </label>

            <label className="field">
              <span>Mértékegység</span>
              <select
                value={editForm.uom_id}
                onChange={(event) =>
                  setEditForm((current) =>
                    current ? { ...current, uom_id: event.target.value } : current
                  )
                }
                className="field-input"
              >
                {unitsOfMeasure.map((item) => (
                  <option key={item.id} value={item.id}>
                    {getUnitOfMeasureLabel(item)}
                  </option>
                ))}
              </select>
            </label>

            <label className="field checkbox-field">
              <span>Készletkezelt</span>
              <input
                type="checkbox"
                checked={editForm.track_stock}
                onChange={(event) =>
                  setEditForm((current) =>
                    current
                      ? { ...current, track_stock: event.target.checked }
                      : current
                  )
                }
              />
            </label>

            <label className="field checkbox-field">
              <span>Aktív</span>
              <input
                type="checkbox"
                checked={editForm.is_active}
                onChange={(event) =>
                  setEditForm((current) =>
                    current ? { ...current, is_active: event.target.checked } : current
                  )
                }
              />
            </label>
          </div>

          <div className="inline-actions">
            <button
              type="button"
              className="primary-button"
              onClick={handleSubmit}
              disabled={isSaving || !editForm.name.trim()}
            >
              Módosítások mentése
            </button>
            <button
              type="button"
              className="secondary-button"
              onClick={cancelEditing}
              disabled={isSaving}
            >
              Mégse
            </button>
          </div>
        </section>
      ) : null}

      <section className="panel">
        <div className="panel-header">
          <h2>Készletelemek listája</h2>
          <span className="panel-count">{items.length}</span>
        </div>

        {!isLoading && items.length === 0 ? (
          <p className="empty-message">
            Nincs készletelem a kiválasztott szűrőkkel.
          </p>
        ) : null}

        {items.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Név</th>
                  <th>Tételtípus</th>
                  <th>Készletkezelt</th>
                  <th>Aktív</th>
                  <th>Létrehozva</th>
                  <th>Frissítve</th>
                  <th>Műveletek</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>{item.name}</td>
                    <td>{formatItemType(item.item_type)}</td>
                    <td>{formatBoolean(item.track_stock)}</td>
                    <td>{formatBoolean(item.is_active)}</td>
                    <td>{formatDateTime(item.created_at)}</td>
                    <td>{formatDateTime(item.updated_at)}</td>
                    <td>
                      <div className="inline-actions">
                        <button
                          type="button"
                          className="secondary-button"
                          onClick={() => startEditing(item)}
                          disabled={isSaving}
                        >
                          Szerkesztés
                        </button>
                        <button
                          type="button"
                          className="secondary-button"
                          onClick={() => handleArchive(item)}
                          disabled={isSaving || !item.is_active}
                        >
                          {item.is_active ? "Archiválás" : "Archiválva"}
                        </button>
                      </div>
                    </td>
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
