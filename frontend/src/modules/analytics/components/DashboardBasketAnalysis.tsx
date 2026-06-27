import { Fragment } from "react";

import { Card } from "../../../shared/components/ui/Card";
import type {
  DashboardBasketPairRow,
  DashboardBasketReceipt,
} from "../types/analytics";
import {
  formatMoney,
  formatNumber,
  formatPaymentMethod,
  toNumber,
} from "./dashboardView";

export function DashboardBasketAnalysis({
  pairs,
  selectedPair,
  setSelectedPair,
  receipts,
  isLoading,
}: {
  pairs: DashboardBasketPairRow[];
  selectedPair: DashboardBasketPairRow | null;
  setSelectedPair: (value: DashboardBasketPairRow | null) => void;
  receipts: DashboardBasketReceipt[];
  isLoading: boolean;
}) {
  const maxRevenue = Math.max(
    ...pairs.map((row) => toNumber(row.total_gross_amount)),
    1,
  );
  const selectedPairKey = selectedPair
    ? `${selectedPair.product_a}-${selectedPair.product_b}`
    : "";

  return (
    <Card
      hoverable
      className="basket-analysis-card"
      eyebrow="Kosárelemzés"
      title="Együtt vásárolt termékek"
      subtitle="Gyakori termékpárok nyugták alapján"
      count={pairs.length}
    >
      <div className="basket-analysis-layout">
        <div className="basket-pair-list">
          {pairs.map((row, index) => {
            const pairKey = `${row.product_a}-${row.product_b}`;
            const revenue = toNumber(row.total_gross_amount);
            const width = `${Math.max(4, (revenue / maxRevenue) * 100)}%`;
            const isSelected = selectedPairKey === pairKey;
            return (
              <Fragment key={pairKey}>
                <button
                  type="button"
                  className={
                    isSelected
                      ? "basket-pair-row basket-pair-row-active"
                      : "basket-pair-row"
                  }
                  onClick={() => setSelectedPair(isSelected ? null : row)}
                >
                  <span className="basket-pair-rank">{index + 1}</span>
                  <span className="basket-pair-content">
                    <span className="basket-pair-title">
                      <strong>{row.product_a}</strong>
                      <span>+</span>
                      <strong>{row.product_b}</strong>
                    </span>
                    <span className="basket-pair-bar">
                      <span style={{ width }} />
                    </span>
                    <span className="basket-pair-meta">
                      <span>{row.basket_count} közös kosár</span>
                      <span>{formatMoney(row.total_gross_amount)}</span>
                    </span>
                  </span>
                </button>

                {isSelected ? (
                  <div className="basket-inline-detail">
                    <div className="basket-inline-summary">
                      <span>
                        <strong>{row.basket_count}</strong>
                        Közös kosár
                      </span>
                      <span>
                        <strong>{formatMoney(row.total_gross_amount)}</strong>
                        Bruttó összeg
                      </span>
                      <span>
                        <strong>{receipts.length}</strong>
                        Kapcsolódó nyugta
                      </span>
                    </div>
                    {isLoading ? (
                      <p className="info-message">Nyugták betöltése...</p>
                    ) : null}
                    <div className="basket-inline-receipts">
                      {receipts.slice(0, 4).map((receipt) => (
                        <article
                          className="basket-inline-receipt"
                          key={receipt.receipt_no}
                        >
                          <span>
                            <strong>{receipt.receipt_no}</strong>
                            {receipt.date ?? "-"}
                          </span>
                          <span>{formatMoney(receipt.gross_amount)}</span>
                          <small>{formatNumber(receipt.quantity)} tétel</small>
                        </article>
                      ))}
                    </div>
                    {receipts.length > 4 ? (
                      <p className="section-note">
                        További {receipts.length - 4} nyugta tartozik ehhez a
                        termékpárhoz.
                      </p>
                    ) : null}
                    {receipts.length === 0 && !isLoading ? (
                      <p className="empty-message">
                        Ehhez a termékpárhoz nincs részletezhető nyugta.
                      </p>
                    ) : null}
                  </div>
                ) : null}
              </Fragment>
            );
          })}
          {pairs.length === 0 ? (
            <p className="info-message">
              Nincs kosárpár ebben az időszakban.
            </p>
          ) : null}
        </div>

        <aside className="basket-detail-card">
          {selectedPair ? (
            <>
              <div className="section-heading-row">
                <div>
                  <h3>
                    {selectedPair.product_a} + {selectedPair.product_b}
                  </h3>
                  <p className="section-note">
                    Kapcsolódó nyugták és tételek
                  </p>
                </div>
                <span className="status-pill">{receipts.length} nyugta</span>
              </div>

              <div className="basket-detail-metrics">
                <span>
                  <strong>{selectedPair.basket_count}</strong>
                  Közös kosár
                </span>
                <span>
                  <strong>{formatMoney(selectedPair.total_gross_amount)}</strong>
                  Bruttó összeg
                </span>
              </div>

              {isLoading ? (
                <p className="info-message">Nyugták betöltése...</p>
              ) : null}

              <div className="basket-receipt-list">
                {receipts.map((receipt) => (
                  <article
                    className="basket-receipt-card"
                    key={receipt.receipt_no}
                  >
                    <div className="activity-meta">
                      <strong>{receipt.receipt_no}</strong>
                      <span>{receipt.date ?? "-"}</span>
                    </div>
                    <p>
                      {formatMoney(receipt.gross_amount)} ·{" "}
                      {formatNumber(receipt.quantity)} tétel
                    </p>
                    <div className="table-wrap basket-receipt-table">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>Termék</th>
                            <th>Kategória</th>
                            <th>Mennyiség</th>
                            <th>Bruttó összeg</th>
                            <th>Fizetés</th>
                          </tr>
                        </thead>
                        <tbody>
                          {receipt.lines.map((line) => (
                            <tr key={line.row_id}>
                              <td>{line.product_name}</td>
                              <td>{line.category_name}</td>
                              <td>{formatNumber(line.quantity)}</td>
                              <td>{formatMoney(line.gross_amount)}</td>
                              <td>
                                {line.payment_method
                                  ? formatPaymentMethod(line.payment_method)
                                  : "-"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </article>
                ))}
              </div>

              {receipts.length === 0 && !isLoading ? (
                <p className="empty-message">
                  Ehhez a termékpárhoz nincs részletezhető nyugta.
                </p>
              ) : null}
            </>
          ) : (
            <div className="basket-detail-empty">
              <strong>Válassz egy termékpárt</strong>
              <span>
                A kapcsolódó nyugták itt, külön részletező panelben jelennek
                meg.
              </span>
            </div>
          )}
        </aside>
      </div>
    </Card>
  );
}
