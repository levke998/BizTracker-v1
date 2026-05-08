import { useEffect } from "react";

import { useTopbarControls } from "../../../shared/components/layout/TopbarControlsContext";
import type { BusinessUnit } from "../../masterData/types/masterData";
import { useTransactions } from "../hooks/useTransactions";
import type { FinancialTransaction } from "../types/finance";

const transactionTypeOptions = [
  { value: "", label: "Minden típus" },
  { value: "pos_sale", label: "Kasszás eladás" },
  { value: "supplier_invoice", label: "Beszerzési számla" },
];

const sourceTypeOptions = [
  { value: "", label: "Minden forrás" },
  { value: "import_row", label: "Importált POS sor" },
  { value: "supplier_invoice", label: "Beszerzési számla" },
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

function formatAmount(amount: string, currency: string) {
  const value = Number(amount);
  if (Number.isNaN(value)) {
    return `${amount} ${currency}`;
  }

  return new Intl.NumberFormat("hu-HU", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value).concat(` ${currency}`);
}

function formatDirection(value: string) {
  const labels: Record<string, string> = {
    inflow: "Bevétel",
    outflow: "Kiadás",
  };
  return labels[value] ?? value;
}

function formatTransactionType(value: string) {
  const labels: Record<string, string> = {
    pos_sale: "Kasszás eladás",
    supplier_invoice: "Beszerzési számla",
  };
  return labels[value] ?? value;
}

function formatSourceType(value: string) {
  const labels: Record<string, string> = {
    import_row: "Importált POS sor",
    supplier_invoice: "Beszerzési számla",
  };
  return labels[value] ?? value;
}

function getDirectionClass(value: string) {
  if (value === "inflow") {
    return "status-pill status-pill-success";
  }
  if (value === "outflow") {
    return "status-pill status-pill-danger";
  }
  return "status-pill";
}

function summarizeTransactions(transactions: FinancialTransaction[]) {
  return transactions.reduce(
    (summary, transaction) => {
      const amount = Number(transaction.amount);
      const safeAmount = Number.isFinite(amount) ? amount : 0;
      if (transaction.direction === "inflow") {
        summary.revenue += safeAmount;
      }
      if (transaction.direction === "outflow") {
        summary.cost += safeAmount;
      }
      return summary;
    },
    { revenue: 0, cost: 0 },
  );
}

function TransactionsHeaderControls({
  primaryBusinessUnits,
  technicalBusinessUnits,
  selectedBusinessUnitId,
  setSelectedBusinessUnitId,
  selectedTransactionType,
  setSelectedTransactionType,
  selectedSourceType,
  setSelectedSourceType,
  limit,
  setLimit,
}: {
  primaryBusinessUnits: BusinessUnit[];
  technicalBusinessUnits: BusinessUnit[];
  selectedBusinessUnitId: string;
  setSelectedBusinessUnitId: (value: string) => void;
  selectedTransactionType: string;
  setSelectedTransactionType: (value: string) => void;
  selectedSourceType: string;
  setSelectedSourceType: (value: string) => void;
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
        <span>Típus</span>
        <select
          value={selectedTransactionType}
          onChange={(event) => setSelectedTransactionType(event.target.value)}
          className="field-input"
        >
          {transactionTypeOptions.map((option) => (
            <option key={option.value || "all"} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label className="field topbar-field">
        <span>Forrás</span>
        <select
          value={selectedSourceType}
          onChange={(event) => setSelectedSourceType(event.target.value)}
          className="field-input"
        >
          {sourceTypeOptions.map((option) => (
            <option key={option.value || "all"} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label className="field topbar-field topbar-field-compact">
        <span>Limit</span>
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

export function TransactionsPage() {
  const { setControls } = useTopbarControls();
  const {
    primaryBusinessUnits,
    technicalBusinessUnits,
    transactions,
    selectedBusinessUnitId,
    setSelectedBusinessUnitId,
    selectedTransactionType,
    setSelectedTransactionType,
    selectedSourceType,
    setSelectedSourceType,
    limit,
    setLimit,
    isLoading,
    errorMessage,
  } = useTransactions();
  const summary = summarizeTransactions(transactions);

  useEffect(() => {
    setControls(
      <TransactionsHeaderControls
        primaryBusinessUnits={primaryBusinessUnits}
        technicalBusinessUnits={technicalBusinessUnits}
        selectedBusinessUnitId={selectedBusinessUnitId}
        setSelectedBusinessUnitId={setSelectedBusinessUnitId}
        selectedTransactionType={selectedTransactionType}
        setSelectedTransactionType={setSelectedTransactionType}
        selectedSourceType={selectedSourceType}
        setSelectedSourceType={setSelectedSourceType}
        limit={limit}
        setLimit={setLimit}
      />,
    );

    return () => setControls(null);
  }, [
    limit,
    primaryBusinessUnits,
    selectedBusinessUnitId,
    selectedSourceType,
    selectedTransactionType,
    setControls,
    setLimit,
    setSelectedBusinessUnitId,
    setSelectedSourceType,
    setSelectedTransactionType,
    technicalBusinessUnits,
  ]);

  return (
    <section className="page-section">
      {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
      {isLoading ? <p className="info-message">Tranzakciók betöltése...</p> : null}

      <div className="finance-summary-grid">
        <article className="finance-summary-card">
          <span>Bevétel</span>
          <strong>{formatAmount(String(summary.revenue), "HUF")}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Kiadás</span>
          <strong>{formatAmount(String(summary.cost), "HUF")}</strong>
        </article>
        <article className="finance-summary-card">
          <span>Találatok</span>
          <strong>{transactions.length}</strong>
        </article>
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Pénzügyi tranzakciók</h2>
          <span className="panel-count">{transactions.length}</span>
        </div>

        {!isLoading && transactions.length === 0 ? (
          <p className="empty-message">
            Nincs pénzügyi tranzakció a kiválasztott szűrőkkel.
          </p>
        ) : null}

        {transactions.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Időpont</th>
                  <th>Összeg</th>
                  <th>Irány</th>
                  <th>Típus</th>
                  <th>Leírás</th>
                  <th>Forrás</th>
                  <th>Forrásazonosító</th>
                  <th>Rögzítve</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((transaction) => (
                  <tr key={transaction.id}>
                    <td>{formatDateTime(transaction.occurred_at)}</td>
                    <td>{formatAmount(transaction.amount, transaction.currency)}</td>
                    <td>
                      <span className={getDirectionClass(transaction.direction)}>
                        {formatDirection(transaction.direction)}
                      </span>
                    </td>
                    <td>{formatTransactionType(transaction.transaction_type)}</td>
                    <td>{transaction.description}</td>
                    <td>{formatSourceType(transaction.source_type)}</td>
                    <td className="mono-cell">{transaction.source_id}</td>
                    <td>{formatDateTime(transaction.created_at)}</td>
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
