"""Pure statistical and recommendation rules for forecast analytics."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any, Callable


def average_decimal(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    return sum(values, Decimal("0")) / Decimal(len(values))


def dominant_label(counts: dict[str, int], *, fallback: str) -> str:
    if not counts:
        return fallback
    return max(counts.items(), key=lambda item: item[1])[0]


def average_revenue_by_key(
    rows: list[dict[str, object]],
    *,
    key_builder: Callable[[dict[str, object]], Any],
) -> dict[Any, Decimal]:
    grouped: dict[Any, list[Decimal]] = defaultdict(list)
    for row in rows:
        grouped[key_builder(row)].append(Decimal(row["revenue"]))
    return {
        key: average_decimal(values) or Decimal("0")
        for key, values in grouped.items()
    }


def average_sales_by_key(
    rows: list[dict[str, object]],
    *,
    key_builder: Callable[[dict[str, object]], Any],
) -> dict[Any, dict[str, Decimal]]:
    grouped: dict[Any, dict[str, list[Decimal]]] = defaultdict(
        lambda: {"revenue": [], "quantity": []}
    )
    for row in rows:
        key = key_builder(row)
        grouped[key]["revenue"].append(Decimal(row["revenue"]))
        grouped[key]["quantity"].append(Decimal(row["quantity"]))
    return {
        key: {
            "revenue": average_decimal(values["revenue"]) or Decimal("0"),
            "quantity": average_decimal(values["quantity"]) or Decimal("0"),
        }
        for key, values in grouped.items()
    }


def average_window_sales_by_key(
    rows: list[dict[str, object]],
    *,
    key_builder: Callable[[dict[str, object]], Any],
) -> dict[Any, dict[str, Decimal]]:
    grouped: dict[Any, dict[str, list[Decimal]]] = defaultdict(
        lambda: {"revenue": [], "quantity": [], "transaction_count": []}
    )
    for row in rows:
        key = key_builder(row)
        grouped[key]["revenue"].append(Decimal(row["revenue"]))
        grouped[key]["quantity"].append(Decimal(row["quantity"]))
        grouped[key]["transaction_count"].append(Decimal(row["transaction_count"]))
    return {
        key: {
            "revenue": average_decimal(values["revenue"]) or Decimal("0"),
            "quantity": average_decimal(values["quantity"]) or Decimal("0"),
            "transaction_count": (
                average_decimal(values["transaction_count"]) or Decimal("0")
            ),
        }
        for key, values in grouped.items()
    }


def dominant_product_categories(
    rows: list[dict[str, object]],
    *,
    fallback: str,
) -> dict[str, str]:
    category_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    for row in rows:
        category_counts[str(row["product_name"])][str(row["category_name"])] += 1
    return {
        product_name: dominant_label(counts, fallback=fallback)
        for product_name, counts in category_counts.items()
    }


def demand_signal(uplift_percent: Decimal) -> str:
    if uplift_percent >= Decimal("20"):
        return "emelkedo"
    if uplift_percent <= Decimal("-15"):
        return "visszafogott"
    return "normal"


def impact_recommendation(
    *,
    scope: str,
    temperature_band: str,
    condition_band: str,
    expected_revenue: Decimal,
    historical_average: Decimal,
) -> str:
    above_average = (
        historical_average > Decimal("0")
        and expected_revenue >= historical_average * Decimal("1.10")
    )
    if scope == "flow":
        if condition_band == "csapadekos":
            return "Esős event-nap lehet: beléptetés, ruhatár és fedett sorbanállás kapjon figyelmet."
        if above_average:
            return "A forecast erős napot jelez: a pult és a személyzet kapacitását érdemes előre emelni."
        return "Az event- és pulttervhez használható időjárási kontextus, kézi ellenőrzéssel."
    if temperature_band == "kanikula":
        return "Kánikula várható: fagyi, hideg ital és gyors pultkapacitás legyen előtérben."
    if condition_band == "csapadekos":
        return "Csapadék várható: a fedett fogyasztás, sütik és meleg italok kaphatnak nagyobb szerepet."
    if above_average:
        return "A hasonló időjárás historikusan erősebb napot hozott: készlet- és termelésemelés javasolt."
    return "Normál készültség javasolt; a forecast frissülésekor a becslés automatikusan változhat."


def category_recommendation(
    *,
    category_name: str,
    temperature_band: str,
    condition_band: str,
    signal: str,
) -> str:
    category = category_name.casefold()
    if "fagyi" in category or "fagylalt" in category:
        if temperature_band in {"meleg", "kanikula"}:
            return "Meleg forecast mellett feltöltött pult és gyors fagylalt-kiszolgálás javasolt."
        if condition_band == "csapadekos":
            return "Csapadékban a fagylaltkészlet frissítési ritmusa legyen kontrollált."
    if "kave" in category or "kávé" in category:
        return "A kávékategória reggeli és délutáni idősávja külön figyelmet érdemel."
    if signal == "emelkedo":
        return "Átlag feletti kereslet várható; készlet- és pultkapacitás-emelés javasolt."
    if signal == "visszafogott":
        return "Visszafogottabb kereslet várható; a termelési mennyiség legyen kontrollált."
    return "Normál kategóriakészültség javasolt a következő forecast-frissítésig."


def product_recommendation(
    *,
    product_name: str,
    signal: str,
    condition_band: str,
) -> str:
    if signal == "emelkedo":
        return f"{product_name}: pultfeltöltés, recept-alapanyag és gyors kiszolgálási készültség javasolt."
    if signal == "visszafogott":
        return f"{product_name}: a friss készletet érdemes kontrolláltan tartani."
    if condition_band == "csapadekos":
        return f"{product_name}: a fedett fogyasztási és elviteles ritmust érdemes figyelni."
    return f"{product_name}: normál termékkészültség javasolt."


def peak_time_recommendation(*, time_window: str, signal: str) -> str:
    if signal == "emelkedo":
        return f"{time_window}: személyzet-, pultfeltöltés- és gyors kiszolgálási előkészítés javasolt."
    if signal == "visszafogott":
        return f"{time_window}: a termelési és pultfeltöltési ritmus legyen óvatosabb."
    return f"{time_window}: normál csúcsidős előkészítés javasolt."
