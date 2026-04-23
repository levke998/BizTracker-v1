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
      setActionMessage(`Inventory item "${payload.name}" updated successfully.`);
      setEditingItemId("");
      setEditForm(null);
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : "Failed to update inventory item."
      );
    }
  };

  const handleCreate = async () => {
    if (!selectedBusinessUnitId) {
      setActionMessage("");
      setActionErrorMessage("Select a business unit before creating an inventory item.");
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
      setActionMessage(`Inventory item "${payload.name}" created successfully.`);
      setCreateForm((current) => ({
        ...current,
        name: "",
        item_type: "raw_material",
        track_stock: true,
        is_active: true,
      }));
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : "Failed to create inventory item."
      );
    }
  };

  const handleArchive = async (item: InventoryItem) => {
    if (!window.confirm(`Archive inventory item "${item.name}"?`)) {
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
      setActionMessage(`Inventory item "${item.name}" archived successfully.`);
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : "Failed to archive inventory item."
      );
    }
  };

  return (
    <section className="page-section">
      <div className="panel">
        <div className="panel-header">
          <h2>Inventory Items</h2>
          <span className="panel-count">{items.length}</span>
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
            <span>Item type</span>
            <select
              value={selectedItemType}
              onChange={(event) => setSelectedItemType(event.target.value)}
              className="field-input"
            >
              <option value="">All item types</option>
              <option value="raw_material">raw_material</option>
              <option value="packaging">packaging</option>
              <option value="finished_good">finished_good</option>
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
        {isLoading ? <p className="info-message">Loading inventory items...</p> : null}
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Create inventory item</h2>
          <span className="panel-count">New</span>
        </div>

        <div className="form-grid inventory-edit-grid">
          <label className="field">
            <span>Name</span>
            <input
              value={createForm.name}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, name: event.target.value }))
              }
              className="field-input"
            />
          </label>

          <label className="field">
            <span>Item type</span>
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
              <option value="raw_material">raw_material</option>
              <option value="packaging">packaging</option>
              <option value="finished_good">finished_good</option>
            </select>
          </label>

          <label className="field">
            <span>Unit of measure</span>
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
            <span>Track stock</span>
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
            <span>Active</span>
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
            Create item
          </button>
        </div>
      </section>

      {editingItem && editForm ? (
        <section className="panel">
          <div className="panel-header">
            <h2>Edit inventory item</h2>
            <span className="panel-count">1</span>
          </div>

          <div className="form-grid inventory-edit-grid">
            <label className="field">
              <span>Name</span>
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
              <span>Item type</span>
              <select
                value={editForm.item_type}
                onChange={(event) =>
                  setEditForm((current) =>
                    current ? { ...current, item_type: event.target.value } : current
                  )
                }
                className="field-input"
              >
                <option value="raw_material">raw_material</option>
                <option value="packaging">packaging</option>
                <option value="finished_good">finished_good</option>
              </select>
            </label>

            <label className="field">
              <span>Unit of measure</span>
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
              <span>Track stock</span>
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
              <span>Active</span>
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
              Save changes
            </button>
            <button
              type="button"
              className="secondary-button"
              onClick={cancelEditing}
              disabled={isSaving}
            >
              Cancel
            </button>
          </div>
        </section>
      ) : null}

      <section className="panel">
        <div className="panel-header">
          <h2>Inventory item list</h2>
          <span className="panel-count">{items.length}</span>
        </div>

        {!isLoading && items.length === 0 ? (
          <p className="empty-message">
            No inventory items found for the selected filters.
          </p>
        ) : null}

        {items.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Item type</th>
                  <th>Track stock</th>
                  <th>Active</th>
                  <th>Created at</th>
                  <th>Updated at</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>{item.name}</td>
                    <td>{item.item_type}</td>
                    <td>{item.track_stock ? "Yes" : "No"}</td>
                    <td>{item.is_active ? "Yes" : "No"}</td>
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
                          Edit
                        </button>
                        <button
                          type="button"
                          className="secondary-button"
                          onClick={() => handleArchive(item)}
                          disabled={isSaving || !item.is_active}
                        >
                          {item.is_active ? "Archive" : "Archived"}
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
