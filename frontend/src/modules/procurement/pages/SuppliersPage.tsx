import { useEffect, useState } from "react";

import { useTopbarControls } from "../../../shared/components/layout/TopbarControlsContext";
import type { BusinessUnit } from "../../masterData/types/masterData";
import type { Supplier, SupplierCreatePayload } from "../types/procurement";
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

const statusOptions = [
  { value: "active", label: "Aktív" },
  { value: "inactive", label: "Inaktív" },
  { value: "all", label: "Összes" },
];

const limitOptions = [25, 50, 100, 200];

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

function getActiveSuppliers(suppliers: Supplier[]) {
  return suppliers.filter((supplier) => supplier.is_active).length;
}

function SuppliersHeaderControls({
  primaryBusinessUnits,
  technicalBusinessUnits,
  selectedBusinessUnitId,
  setSelectedBusinessUnitId,
  selectedStatus,
  setSelectedStatus,
  limit,
  setLimit,
}: {
  primaryBusinessUnits: BusinessUnit[];
  technicalBusinessUnits: BusinessUnit[];
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  selectedStatus: string;
  setSelectedStatus: (value: string) => void;
  limit: number;
  setLimit: (value: number) => void;
}) {
  return (
    <div className="business-dashboard-filters topbar-dashboard-filters">
      <label className="field topbar-field">
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
            <optgroup label="Technikai adatok">
              {technicalBusinessUnits.map((businessUnit) => (
                <option key={businessUnit.id} value={businessUnit.id}>
                  {businessUnit.name} ({businessUnit.code})
                </option>
              ))}
            </optgroup>
          ) : null}
        </select>
      </label>

      <label className="field topbar-field">
        <span>Státusz</span>
        <select
          value={selectedStatus}
          onChange={(event) => setSelectedStatus(event.target.value)}
          className="field-input"
        >
          {statusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label className="field topbar-field topbar-field-compact">
        <span>Találat</span>
        <select
          value={String(limit)}
          onChange={(event) => setLimit(Number(event.target.value))}
          className="field-input"
        >
          {limitOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}

export function SuppliersPage() {
  const { setControls } = useTopbarControls();
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
  const activeSuppliers = getActiveSuppliers(suppliers);

  useEffect(() => {
    setControls(
      <SuppliersHeaderControls
        primaryBusinessUnits={primaryBusinessUnits}
        technicalBusinessUnits={technicalBusinessUnits}
        selectedBusinessUnitId={selectedBusinessUnitId}
        setSelectedBusinessUnitId={setSelectedBusinessUnitId}
        selectedStatus={selectedStatus}
        setSelectedStatus={setSelectedStatus}
        limit={limit}
        setLimit={setLimit}
      />,
    );

    return () => setControls(null);
  }, [
    limit,
    primaryBusinessUnits,
    selectedBusinessUnitId,
    selectedStatus,
    setControls,
    setLimit,
    setSelectedBusinessUnitId,
    setSelectedStatus,
    technicalBusinessUnits,
  ]);

  const handleCreate = async () => {
    if (!selectedBusinessUnitId) {
      setActionMessage("");
      setActionErrorMessage("Beszállító létrehozásához válassz vállalkozást.");
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
      setActionMessage(`A(z) "${payload.name}" beszállító létrejött.`);
      setCreateForm({
        ...INITIAL_FORM,
        is_active: createForm.is_active,
      });
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : "Nem sikerült létrehozni a beszállítót."
      );
    }
  };

  return (
    <section className="page-section">
      {actionMessage ? <p className="success-message">{actionMessage}</p> : null}
      {actionErrorMessage ? <p className="error-message">{actionErrorMessage}</p> : null}
      {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
      {isLoading ? <p className="info-message">Beszállítók betöltése...</p> : null}

      <div className="finance-summary-grid">
        <article className="finance-summary-card">
          <span>Aktív beszállítók</span>
          <strong>{activeSuppliers}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Találatok</span>
          <strong>{suppliers.length}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Szűrés</span>
          <strong>
            {statusOptions.find((option) => option.value === selectedStatus)?.label ??
              "Összes"}
          </strong>
        </article>
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Új beszállító</h2>
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
            <span>Adószám</span>
            <input
              value={createForm.tax_id}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, tax_id: event.target.value }))
              }
              className="field-input"
            />
          </label>

          <label className="field">
            <span>Kapcsolattartó</span>
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
            <span>Telefon</span>
            <input
              value={createForm.phone}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, phone: event.target.value }))
              }
              className="field-input"
            />
          </label>

          <label className="field">
            <span>Megjegyzés</span>
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
            disabled={isSaving || !selectedBusinessUnitId || !createForm.name.trim()}
          >
            Beszállító létrehozása
          </button>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Beszállítók</h2>
          <span className="panel-count">{suppliers.length}</span>
        </div>

        {!isLoading && suppliers.length === 0 ? (
          <p className="empty-message">Nincs beszállító a kiválasztott szűrőkkel.</p>
        ) : null}

        {suppliers.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Név</th>
                  <th>Adószám</th>
                  <th>Kapcsolattartó</th>
                  <th>Email</th>
                  <th>Telefon</th>
                  <th>Státusz</th>
                  <th>Frissítve</th>
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
                    <td>
                      <span
                        className={
                          supplier.is_active
                            ? "status-pill status-pill-success"
                            : "status-pill"
                        }
                      >
                        {supplier.is_active ? "Aktív" : "Inaktív"}
                      </span>
                    </td>
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
