import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "../../../shared/components/ui/Button";
import { Card } from "../../../shared/components/ui/Card";
import { listBusinessUnits } from "../../masterData/api/masterDataApi";
import { createDemoPosReceipt, listDemoPosCatalog } from "../api/demoPosApi";
import type { DemoPosCatalogProduct, DemoPosReceipt } from "../types/demoPos";

type CartLine = {
  product: DemoPosCatalogProduct;
  quantity: number;
};

const paymentMethods = ["card", "cash", "szep_card"];

function toNumber(value: string | number | null | undefined) {
  const parsed = Number(value ?? 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatMoney(value: string | number) {
  return new Intl.NumberFormat("hu-HU", {
    style: "currency",
    currency: "HUF",
    maximumFractionDigits: 0,
  }).format(typeof value === "number" ? value : toNumber(value));
}

function groupProducts(products: DemoPosCatalogProduct[]) {
  return products.reduce<Record<string, DemoPosCatalogProduct[]>>((groups, product) => {
    const key = product.category_name ?? "Egyeb";
    groups[key] = [...(groups[key] ?? []), product];
    return groups;
  }, {});
}

function pickRandom<T>(items: T[]) {
  return items[Math.floor(Math.random() * items.length)];
}

function buildReceiptNo(businessUnitCode: string) {
  const now = new Date();
  const stamp = [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, "0"),
    String(now.getDate()).padStart(2, "0"),
    String(now.getHours()).padStart(2, "0"),
    String(now.getMinutes()).padStart(2, "0"),
    String(now.getSeconds()).padStart(2, "0"),
  ].join("");
  return `POS-${businessUnitCode.toUpperCase()}-${stamp}-${Math.random()
    .toString(16)
    .slice(2, 6)
    .toUpperCase()}`;
}

export function DemoPosPage() {
  const queryClient = useQueryClient();
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [paymentMethod, setPaymentMethod] = useState("card");
  const [cart, setCart] = useState<CartLine[]>([]);
  const [autoMode, setAutoMode] = useState(false);
  const [lastReceipts, setLastReceipts] = useState<DemoPosReceipt[]>([]);
  const autoTimerRef = useRef<number | null>(null);

  const businessUnitsQuery = useQuery({
    queryKey: ["business-units"],
    queryFn: listBusinessUnits,
  });

  const businessUnits = businessUnitsQuery.data ?? [];
  const selectedBusinessUnit =
    businessUnits.find((unit) => unit.id === selectedBusinessUnitId) ?? businessUnits[0];

  useEffect(() => {
    if (!selectedBusinessUnitId && businessUnits.length > 0) {
      setSelectedBusinessUnitId(businessUnits[0].id);
    }
  }, [businessUnits, selectedBusinessUnitId]);

  const catalogQuery = useQuery({
    queryKey: ["demo-pos-catalog", selectedBusinessUnit?.id],
    queryFn: () => listDemoPosCatalog(selectedBusinessUnit!.id),
    enabled: Boolean(selectedBusinessUnit?.id),
  });

  const products = catalogQuery.data ?? [];
  const groupedProducts = useMemo(() => groupProducts(products), [products]);
  const categories = Object.keys(groupedProducts);
  const visibleProducts =
    selectedCategory === "all"
      ? products
      : products.filter((product) => product.category_name === selectedCategory);
  const cartTotal = cart.reduce(
    (total, line) => total + toNumber(line.product.sale_price_gross) * line.quantity,
    0,
  );
  const cartItems = cart.reduce((total, line) => total + line.quantity, 0);

  const receiptMutation = useMutation({
    mutationFn: createDemoPosReceipt,
    onSuccess: (receipt) => {
      setLastReceipts((current) => [receipt, ...current].slice(0, 8));
      setCart([]);
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["finance-transactions"] });
      void queryClient.invalidateQueries({ queryKey: ["import-batches"] });
    },
  });

  function addToCart(product: DemoPosCatalogProduct) {
    setCart((current) => {
      const existing = current.find((line) => line.product.id === product.id);
      if (existing) {
        return current.map((line) =>
          line.product.id === product.id
            ? { ...line, quantity: Math.min(line.quantity + 1, 99) }
            : line,
        );
      }
      return [...current, { product, quantity: 1 }];
    });
  }

  function updateQuantity(productId: string, quantity: number) {
    if (quantity <= 0) {
      setCart((current) => current.filter((line) => line.product.id !== productId));
      return;
    }

    setCart((current) =>
      current.map((line) =>
        line.product.id === productId ? { ...line, quantity: Math.min(quantity, 99) } : line,
      ),
    );
  }

  function submitCart(lines: CartLine[]) {
    if (!selectedBusinessUnit || lines.length === 0) {
      return;
    }

    receiptMutation.mutate({
      business_unit_id: selectedBusinessUnit.id,
      receipt_no: buildReceiptNo(selectedBusinessUnit.code),
      payment_method: paymentMethod,
      occurred_at: new Date().toISOString(),
      lines: lines.map((line) => ({
        product_id: line.product.id,
        quantity: line.quantity,
      })),
    });
  }

  function generateRandomCart() {
    if (products.length === 0) {
      return [];
    }

    const lineCount = Math.min(products.length, Math.floor(Math.random() * 4) + 1);
    const picked = new Map<string, CartLine>();
    while (picked.size < lineCount) {
      const product = pickRandom(products);
      picked.set(product.id, {
        product,
        quantity: Math.floor(Math.random() * 3) + 1,
      });
    }
    return [...picked.values()];
  }

  function sendRandomReceipt() {
    submitCart(generateRandomCart());
  }

  useEffect(() => {
    if (!autoMode) {
      if (autoTimerRef.current) {
        window.clearInterval(autoTimerRef.current);
        autoTimerRef.current = null;
      }
      return;
    }

    autoTimerRef.current = window.setInterval(() => {
      sendRandomReceipt();
    }, 3500);

    return () => {
      if (autoTimerRef.current) {
        window.clearInterval(autoTimerRef.current);
        autoTimerRef.current = null;
      }
    };
  }, [autoMode, products, selectedBusinessUnit?.id, paymentMethod]);

  return (
    <div className="page-stack demo-pos-page">
      <div className="page-header">
        <div>
          <span className="page-eyebrow">Demo POS</span>
          <h1>Teszt kassza</h1>
          <p>
            Valos nyugtaszeru POS sorokat kuld az import es finance pipeline-ba, hogy a
            dashboard azonnal friss adatbol dolgozzon.
          </p>
        </div>
        <div className="demo-pos-header-actions">
          <select
            value={selectedBusinessUnit?.id ?? ""}
            onChange={(event) => {
              setSelectedBusinessUnitId(event.target.value);
              setCart([]);
              setSelectedCategory("all");
            }}
          >
            {businessUnits.map((unit) => (
              <option key={unit.id} value={unit.id}>
                {unit.name}
              </option>
            ))}
          </select>
          <Button
            variant={autoMode ? "secondary" : "primary"}
            onClick={() => setAutoMode((value) => !value)}
            disabled={products.length === 0 || receiptMutation.isPending}
          >
            {autoMode ? "Auto stop" : "Auto sales"}
          </Button>
        </div>
      </div>

      <section className="demo-pos-grid">
        <div className="demo-pos-main">
          <Card
            title="Termekkatalogus"
            subtitle={`${visibleProducts.length} eladhato termek`}
            actions={
              <div className="demo-pos-category-tabs">
                <button
                  className={selectedCategory === "all" ? "active" : ""}
                  onClick={() => setSelectedCategory("all")}
                >
                  Mind
                </button>
                {categories.map((category) => (
                  <button
                    key={category}
                    className={selectedCategory === category ? "active" : ""}
                    onClick={() => setSelectedCategory(category)}
                  >
                    {category}
                  </button>
                ))}
              </div>
            }
          >
            {catalogQuery.isLoading ? (
              <div className="empty-state">Katalogus betoltese...</div>
            ) : (
              <div className="demo-pos-product-grid">
                {visibleProducts.map((product) => (
                  <button
                    key={product.id}
                    type="button"
                    className="demo-pos-product"
                    onClick={() => addToCart(product)}
                  >
                    <span>{product.category_name}</span>
                    <strong>{product.name}</strong>
                    <em>
                      {formatMoney(product.sale_price_gross)}
                      {product.sales_uom_symbol ?? product.sales_uom_code
                        ? ` / ${product.sales_uom_symbol ?? product.sales_uom_code}`
                        : ""}
                    </em>
                  </button>
                ))}
              </div>
            )}
          </Card>
        </div>

        <aside className="demo-pos-side">
          <Card
            title="Kosar"
            subtitle={`${cartItems} tetel`}
            count={formatMoney(cartTotal)}
            tone="primary"
          >
            <div className="demo-pos-payment-row">
              {paymentMethods.map((method) => (
                <button
                  key={method}
                  className={paymentMethod === method ? "active" : ""}
                  onClick={() => setPaymentMethod(method)}
                >
                  {method}
                </button>
              ))}
            </div>

            <div className="demo-pos-cart-list">
              {cart.length === 0 ? (
                <div className="empty-state">Valassz termeket vagy indits random nyugtat.</div>
              ) : (
                cart.map((line) => (
                  <div className="demo-pos-cart-line" key={line.product.id}>
                    <div>
                      <strong>{line.product.name}</strong>
                      <span>{formatMoney(line.product.sale_price_gross)}</span>
                    </div>
                    <div className="demo-pos-stepper">
                      <button onClick={() => updateQuantity(line.product.id, line.quantity - 1)}>
                        -
                      </button>
                      <input
                        value={line.quantity}
                        onChange={(event) =>
                          updateQuantity(line.product.id, Number(event.target.value))
                        }
                      />
                      <button onClick={() => updateQuantity(line.product.id, line.quantity + 1)}>
                        +
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>

            {receiptMutation.error ? (
              <div className="form-error">{receiptMutation.error.message}</div>
            ) : null}

            <div className="demo-pos-actions">
              <Button
                variant="secondary"
                onClick={sendRandomReceipt}
                disabled={receiptMutation.isPending || products.length === 0}
              >
                Random nyugta
              </Button>
              <Button
                glow
                onClick={() => submitCart(cart)}
                disabled={receiptMutation.isPending || cart.length === 0}
              >
                Nyugta kuldese
              </Button>
            </div>
          </Card>

          <Card title="Utolso nyugtak" subtitle="API-n bekuldott demo eladasok">
            <div className="demo-pos-receipts">
              {lastReceipts.length === 0 ? (
                <div className="empty-state">Meg nincs bekuldott nyugta.</div>
              ) : (
                lastReceipts.map((receipt) => (
                  <div className="demo-pos-receipt" key={receipt.batch_id}>
                    <div>
                      <strong>{receipt.receipt_no}</strong>
                      <span>{receipt.transaction_count} sor</span>
                    </div>
                    <em>{formatMoney(receipt.gross_total)}</em>
                  </div>
                ))
              )}
            </div>
          </Card>
        </aside>
      </section>
    </div>
  );
}
