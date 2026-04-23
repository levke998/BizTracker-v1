import { useState } from "react";

import type { SupplierCreatePayload } from "../types/procurement";
import { useSuppliers } from "../hooks/useSuppliers";

type SupplierFormState = {
  name: string;
  tax_id: string;
  contact_name: string;
  email: string;
  phone: string;
  notes: string;
  is_active: boolean;
};

const INITIAL_FORM: SupplierFormState = {
  name: "",
  tax_id: "",
  contact_name: "",
  email: "",
  phone: "",
  notes: "",
  is_active: true,
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

function toOptionalValue(value: string) {
  const trimmedValue = value.trim();
  return trimmedValue.length > 0 ? trimmedValue : undefined;
}

export function SuppliersPage() {
  const {
    primaryBusinessUnits,
    technicalBusinessUnits,
    suppliers,
    selectedBusinessUnitId,
    setSelectedBusinessUnitId,
    selectedStatus,
    setSelectedStatus,
    limit,
    setLimit,
    createSupplier,
    isSaving,
    isLoading,
    errorMessage,
  } = useSuppliers();

  const [createForm, setCreateForm] = useState<SupplierFormState>(INITIAL_FORM);
  const [actionMessage, setActionMessage] = useState("");
  const [actionErrorMessage, setActionErrorMessage] = useState("");

  const handleCreate = async () => {
    if (!selectedBusinessUnitId) {
      setActionMessage("");
      setActionErrorMessage("Select a business unit before creating a supplier.");
      return;
    }

    const payload: SupplierCreatePayload = {
      business_unit_id: selectedBusinessUnitId,
      name: createForm.name.trim(),
      tax_id: toOptionalValue(createForm.tax_id),
      contact_name: toOptionalValue(createForm.contact_name),
      email: toOptionalValue(createForm.email),
      phone: toOptionalValue(createForm.phone),
      notes: toOptionalValue(createForm.notes),
      is_active: createForm.is_active,
    };

    setActionMessage("");
    setActionErrorMessage("");

    try {
      await createSupplier(payload);
      setActionMessage(`Supplier "${payload.name}" created successfully.`);
      setCreateForm({
        ...INITIAL_FORM,
        is_active: createForm.is_active,
      });
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : "Failed to create supplier."
      );
    }
  };

  return (
    <section className="page-section">
      <section className="panel">
        <div className="panel-header">
          <h2>Suppliers</h2>
          <span className="panel-count">{suppliers.length}</span>
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
            <span>Status</span>
            <select
              value={selectedStatus}
              onChange={(event) => setSelectedStatus(event.target.value)}
              className="field-input"
            >
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="all">All</option>
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
        {isLoading ? <p className="info-message">Loading suppliers...</p> : null}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Create supplier</h2>
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
            <span>Tax ID</span>
            <input
              value={createForm.tax_id}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, tax_id: event.target.value }))
              }
              className="field-input"
            />
          </label>

          <label className="field">
            <span>Contact name</span>
            <input
              value={createForm.contact_name}
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  contact_name: event.target.value,
                }))
              }
              className="field-input"
            />
          </label>

          <label className="field">
            <span>Email</span>
            <input
              value={createForm.email}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, email: event.target.value }))
              }
              className="field-input"
            />
          </label>

          <label className="field">
            <span>Phone</span>
            <input
              value={createForm.phone}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, phone: event.target.value }))
              }
              className="field-input"
            />
          </label>

          <label className="field">
            <span>Notes</span>
            <textarea
              value={createForm.notes}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, notes: event.target.value }))
              }
              className="field-input"
              rows={3}
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
            disabled={isSaving || !selectedBusinessUnitId || !createForm.name.trim()}
          >
            Create supplier
          </button>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Supplier list</h2>
          <span className="panel-count">{suppliers.length}</span>
        </div>

        {!isLoading && suppliers.length === 0 ? (
          <p className="empty-message">No suppliers found for the selected filters.</p>
        ) : null}

        {suppliers.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Tax ID</th>
                  <th>Contact</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Active</th>
                  <th>Updated at</th>
                </tr>
              </thead>
              <tbody>
                {suppliers.map((supplier) => (
                  <tr key={supplier.id}>
                    <td>{supplier.name}</td>
                    <td>{supplier.tax_id || "—"}</td>
                    <td>{supplier.contact_name || "—"}</td>
                    <td>{supplier.email || "—"}</td>
                    <td>{supplier.phone || "—"}</td>
                    <td>{supplier.is_active ? "Yes" : "No"}</td>
                    <td>{formatDateTime(supplier.updated_at)}</td>
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
