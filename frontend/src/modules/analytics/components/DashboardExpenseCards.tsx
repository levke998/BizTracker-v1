import { Button } from "../../../shared/components/ui/Button";
import { Card } from "../../../shared/components/ui/Card";
import type {
  DashboardExpenseDetailRow,
  DashboardExpenseRow,
  DashboardExpenseSource,
} from "../types/analytics";
import {
  formatAmountBasis,
  formatMoney,
  formatNumber,
  formatSourceType,
  formatTaxBreakdownSource,
  formatTransactionType,
  toNumber,
} from "./dashboardView";

export function DashboardExpenseBreakdown({
  rows,
  activeType,
  openExpenseType,
}: {
  rows: DashboardExpenseRow[];
  activeType: string | null;
  openExpenseType: (type: string) => void;
}) {
  const total = rows.reduce((sum, row) => sum + toNumber(row.gross_amount), 0);
  const totalNet = rows.reduce(
    (sum, row) => sum + toNumber(row.net_amount ?? "0"),
    0,
  );
  const totalVat = rows.reduce(
    (sum, row) => sum + toNumber(row.vat_amount ?? "0"),
    0,
  );
  const hasTaxBreakdown = rows.some(
    (row) => row.net_amount !== null || row.vat_amount !== null,
  );
  const maxAmount = Math.max(
    ...rows.map((row) => toNumber(row.gross_amount)),
    1,
  );

  return (
    <Card
      tone="highlight"
      hoverable
      eyebrow="Költségkontroll"
      title="Kiadások bontása"
      subtitle="Rögzített kiadások tranzakciótípus szerint"
      count={rows.length}
    >
      <div className="expense-summary-strip">
        <span>
          <strong>{formatMoney(total)}</strong>
          <small>Bruttó tényleges</small>
          Összes kiadás
        </span>
        {hasTaxBreakdown ? (
          <>
            <span>
              <strong>{formatMoney(totalNet)}</strong>
              Nettó
            </span>
            <span>
              <strong>{formatMoney(totalVat)}</strong>
              ÁFA
            </span>
          </>
        ) : null}
        <span>
          <strong>
            {rows.reduce((sum, row) => sum + row.transaction_count, 0)}
          </strong>
          Tranzakció
        </span>
      </div>

      <div className="expense-breakdown-list">
        {rows.map((row) => {
          const width = `${Math.max(
            4,
            (toNumber(row.gross_amount) / maxAmount) * 100,
          )}%`;
          return (
            <button
              key={row.label}
              type="button"
              className={
                activeType === row.label
                  ? "expense-breakdown-row expense-breakdown-row-active"
                  : "expense-breakdown-row"
              }
              onClick={() => openExpenseType(row.label)}
            >
              <span className="expense-breakdown-top">
                <strong>{formatTransactionType(row.label)}</strong>
                <strong>{formatMoney(row.gross_amount)}</strong>
              </span>
              <span className="expense-breakdown-bar">
                <span style={{ width }} />
              </span>
              <span className="expense-breakdown-meta">
                <span>{row.transaction_count} tranzakció</span>
                <span>
                  {formatAmountBasis(row.amount_basis)} ·{" "}
                  {formatTaxBreakdownSource(row.tax_breakdown_source)}
                </span>
              </span>
              {row.net_amount !== null || row.vat_amount !== null ? (
                <span className="expense-breakdown-meta">
                  <span>Nettó: {formatMoney(row.net_amount ?? 0)}</span>
                  <span>ÁFA: {formatMoney(row.vat_amount ?? 0)}</span>
                </span>
              ) : null}
            </button>
          );
        })}
        {rows.length === 0 ? (
          <p className="empty-message">
            Nincs rögzített kiadás ebben az időszakban.
          </p>
        ) : null}
      </div>
    </Card>
  );
}

export function DashboardExpenseDrilldown({
  type,
  rows,
  selectedExpense,
  setSelectedExpense,
  source,
  isLoading,
  close,
}: {
  type: string;
  rows: DashboardExpenseDetailRow[];
  selectedExpense: DashboardExpenseDetailRow | null;
  setSelectedExpense: (value: DashboardExpenseDetailRow) => void;
  source: DashboardExpenseSource | null;
  isLoading: boolean;
  close: () => void;
}) {
  return (
    <Card
      hoverable
      className="expense-detail-card"
      eyebrow="Költségrészletek"
      title={formatTransactionType(type)}
      subtitle="Kiadási tranzakciók és forrásadatok"
      actions={
        <Button variant="secondary" onClick={close}>
          Bezárás
        </Button>
      }
    >
      {isLoading ? <p className="info-message">Részletek betöltése...</p> : null}
      <div className="expense-detail-layout">
        <div className="expense-transaction-list">
          {rows.map((row) => (
            <button
              key={row.transaction_id}
              type="button"
              className={
                selectedExpense?.transaction_id === row.transaction_id
                  ? "expense-transaction-row expense-transaction-row-active"
                  : "expense-transaction-row"
              }
              onClick={() => setSelectedExpense(row)}
            >
              <span>
                <strong>{formatMoney(row.gross_amount)}</strong>
                <small>{row.occurred_at}</small>
              </span>
              <span>
                {row.description ||
                  formatTransactionType(row.transaction_type)}
              </span>
              <small>
                {formatSourceType(row.source_type)} ·{" "}
                {formatTaxBreakdownSource(row.tax_breakdown_source)}
              </small>
            </button>
          ))}
          {rows.length === 0 && !isLoading ? (
            <p className="empty-message">Nincs részletezhető tranzakció.</p>
          ) : null}
        </div>

        <aside className="expense-source-card">
          {selectedExpense && source ? (
            <>
              <div className="section-heading-row">
                <div>
                  <h3>
                    {source.invoice_number ??
                      formatSourceType(source.source_type)}
                  </h3>
                  <p className="section-note">
                    {source.supplier_name ?? "Forrásrekord"} ·{" "}
                    {source.invoice_date ?? source.occurred_at}
                  </p>
                </div>
                <span className="status-pill">{source.lines.length} sor</span>
              </div>

              <div className="expense-source-metrics">
                <article className="detail-item">
                  <span>Bruttó összeg</span>
                  <strong>
                    {source.gross_total
                      ? formatMoney(source.gross_total)
                      : formatMoney(source.gross_amount)}
                  </strong>
                </article>
                <article className="detail-item">
                  <span>Nettó</span>
                  <strong>
                    {source.net_total ? formatMoney(source.net_total) : "-"}
                  </strong>
                </article>
                <article className="detail-item">
                  <span>ÁFA</span>
                  <strong>
                    {source.vat_total ? formatMoney(source.vat_total) : "-"}
                  </strong>
                </article>
                <article className="detail-item">
                  <span>Forrás</span>
                  <strong>
                    {formatTaxBreakdownSource(source.tax_breakdown_source)}
                  </strong>
                </article>
              </div>

              {source.lines.length > 0 ? (
                <div className="table-wrap expense-source-table">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Leírás</th>
                        <th>Mennyiség</th>
                        <th>Nettó egységár</th>
                        <th>Nettó sorösszeg</th>
                        <th>Készletelem</th>
                      </tr>
                    </thead>
                    <tbody>
                      {source.lines.map((line) => (
                        <tr key={line.line_id}>
                          <td>{line.description}</td>
                          <td>{formatNumber(line.quantity)}</td>
                          <td>{formatMoney(line.unit_net_amount)}</td>
                          <td>{formatMoney(line.line_net_amount)}</td>
                          <td>{line.inventory_item_id ?? "-"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="info-message">
                  Ehhez a tranzakcióhoz nincs strukturált forrássor.
                </p>
              )}
            </>
          ) : (
            <div className="expense-source-empty">
              <strong>Válassz egy tranzakciót</strong>
              <span>A forrásrekord és a számlasorok itt jelennek meg.</span>
            </div>
          )}
        </aside>
      </div>
    </Card>
  );
}
