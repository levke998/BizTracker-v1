import { useTransactions } from "../hooks/useTransactions";

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

export function TransactionsPage() {
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

  return (
    <section className="page-section">
      <div className="panel">
        <div className="panel-header">
          <h2>Financial Transactions</h2>
          <span className="panel-count">{transactions.length}</span>
        </div>

        <div className="form-grid finance-filter-grid">
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
            <span>Transaction type</span>
            <select
              value={selectedTransactionType}
              onChange={(event) => setSelectedTransactionType(event.target.value)}
              className="field-input"
            >
              <option value="">All transaction types</option>
              <option value="pos_sale">pos_sale</option>
            </select>
          </label>

          <label className="field">
            <span>Source type</span>
            <select
              value={selectedSourceType}
              onChange={(event) => setSelectedSourceType(event.target.value)}
              className="field-input"
            >
              <option value="">All source types</option>
              <option value="import_row">import_row</option>
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

        {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
        {isLoading ? <p className="info-message">Loading transactions...</p> : null}
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Transaction list</h2>
          <span className="panel-count">{transactions.length}</span>
        </div>

        {!isLoading && transactions.length === 0 ? (
          <p className="empty-message">
            No financial transactions found for the selected filters.
          </p>
        ) : null}

        {transactions.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Occurred at</th>
                  <th>Amount</th>
                  <th>Direction</th>
                  <th>Type</th>
                  <th>Description</th>
                  <th>Source type</th>
                  <th>Source id</th>
                  <th>Created at</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((transaction) => (
                  <tr key={transaction.id}>
                    <td>{formatDateTime(transaction.occurred_at)}</td>
                    <td>{formatAmount(transaction.amount, transaction.currency)}</td>
                    <td>{transaction.direction}</td>
                    <td>{transaction.transaction_type}</td>
                    <td>{transaction.description}</td>
                    <td>{transaction.source_type}</td>
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
