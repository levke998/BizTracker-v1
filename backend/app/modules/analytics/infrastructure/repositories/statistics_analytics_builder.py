"""Dashboard descriptive statistics and data-quality read-model builder."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any
from zoneinfo import ZoneInfo

from app.modules.analytics.domain.entities.dashboard_snapshot import (
    DashboardDemandPercentileRow,
    DashboardInventoryTurnoverReadiness,
    DashboardStatisticsInsight,
    DashboardStatisticsQuality,
    DashboardStatisticsOutlierFlag,
    DashboardStatisticsTrendPoint,
)
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel


class DashboardStatisticsAnalyticsBuilder:
    """Build explainable statistics for Dashboard 2.0 decision support."""

    def __init__(self, *, time_zone: ZoneInfo) -> None:
        self._time_zone = time_zone

    def build_quality(
        self,
        *,
        rows: list[ImportRowModel],
        start_at: datetime,
        end_at: datetime,
    ) -> DashboardStatisticsQuality:
        daily_revenue: dict[date, Decimal] = defaultdict(lambda: Decimal("0"))
        daily_basket_values: dict[date, list[Decimal]] = defaultdict(list)
        baskets: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        basket_dates: dict[str, date] = {}
        category_daily_quantity: dict[str, dict[date, Decimal]] = defaultdict(
            lambda: defaultdict(lambda: Decimal("0"))
        )
        category_totals: dict[str, dict[str, Decimal | int]] = defaultdict(
            lambda: {
                "quantity": Decimal("0"),
                "gross_revenue": Decimal("0"),
                "transaction_count": 0,
            }
        )
        product_daily_quantity: dict[str, dict[date, Decimal]] = defaultdict(
            lambda: defaultdict(lambda: Decimal("0"))
        )
        product_totals: dict[str, dict[str, Decimal | int]] = defaultdict(
            lambda: {
                "quantity": Decimal("0"),
                "gross_revenue": Decimal("0"),
                "transaction_count": 0,
            }
        )
        pos_row_count = 0

        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None or occurred_at < start_at or occurred_at > end_at:
                continue

            gross_amount = self._parse_decimal(payload.get("gross_amount"))
            quantity = self._parse_decimal(payload.get("quantity"))
            business_date = occurred_at.astimezone(self._time_zone).date()
            basket_key = self._basket_key(row, payload)
            daily_revenue[business_date] += gross_amount
            baskets[basket_key] += gross_amount
            basket_dates[basket_key] = business_date
            self._add_demand(
                daily_quantity=category_daily_quantity,
                totals=category_totals,
                label=self._payload_label(payload, "category_name", "Kategoria nelkul"),
                business_date=business_date,
                quantity=quantity,
                gross_amount=gross_amount,
            )
            self._add_demand(
                daily_quantity=product_daily_quantity,
                totals=product_totals,
                label=self._payload_label(payload, "product_name", "Ismeretlen termek"),
                business_date=business_date,
                quantity=quantity,
                gross_amount=gross_amount,
            )
            pos_row_count += 1

        for basket_key, basket_amount in baskets.items():
            basket_date = basket_dates.get(basket_key)
            if basket_date is not None:
                daily_basket_values[basket_date].append(basket_amount)

        daily_values = list(daily_revenue.values())
        basket_values = list(baskets.values())
        period_day_count = max((end_at.date() - start_at.date()).days + 1, 1)
        active_sales_day_count = len(daily_values)
        coverage_percent = self._percent(
            Decimal(active_sales_day_count),
            Decimal(period_day_count),
        )
        quality_level = self._quality_level(
            active_sales_day_count=active_sales_day_count,
            basket_count=len(basket_values),
            coverage_percent=coverage_percent,
        )
        calendar_dates = self._period_dates(start_at.date(), end_at.date())
        rolling_points = tuple(
            self._build_rolling_points(
                calendar_dates=calendar_dates,
                daily_revenue=daily_revenue,
                daily_basket_values=daily_basket_values,
            )
        )
        trend_direction, trend_stability, trend_change_percent, volatility_percent = (
            self._trend_status(
                values=[point.daily_revenue for point in rolling_points],
                active_sales_day_count=active_sales_day_count,
            )
        )
        outlier_flags = tuple(
            self._build_outlier_flags(
                calendar_dates=calendar_dates,
                daily_revenue=daily_revenue,
                basket_values=basket_values,
                quality_level=quality_level,
            )
        )
        category_percentiles = tuple(
            self._build_demand_percentiles(
                scope="category",
                daily_quantity=category_daily_quantity,
                totals=category_totals,
            )
        )
        product_percentiles = tuple(
            self._build_demand_percentiles(
                scope="product",
                daily_quantity=product_daily_quantity,
                totals=product_totals,
            )
        )
        inventory_turnover_readiness = self._inventory_turnover_readiness(
            pos_row_count=pos_row_count,
            product_demand_row_count=len(product_percentiles),
            category_demand_row_count=len(category_percentiles),
            quality_level=quality_level,
        )
        insights = tuple(
            self._build_insights(
                quality_level=quality_level,
                coverage_percent=coverage_percent,
                trend_direction=trend_direction,
                trend_stability=trend_stability,
                trend_change_percent=trend_change_percent,
                volatility_percent=volatility_percent,
                outlier_flags=outlier_flags,
                product_percentiles=product_percentiles,
                category_percentiles=category_percentiles,
                inventory_turnover_readiness=inventory_turnover_readiness,
            )
        )

        return DashboardStatisticsQuality(
            period_day_count=period_day_count,
            active_sales_day_count=active_sales_day_count,
            pos_row_count=pos_row_count,
            basket_count=len(basket_values),
            coverage_percent=coverage_percent,
            quality_level=quality_level,
            average_daily_revenue=self._average(daily_values),
            median_daily_revenue=self._quantile(daily_values, Decimal("0.50")),
            p25_daily_revenue=self._quantile(daily_values, Decimal("0.25")),
            p75_daily_revenue=self._quantile(daily_values, Decimal("0.75")),
            p90_daily_revenue=self._quantile(daily_values, Decimal("0.90")),
            p95_daily_revenue=self._quantile(daily_values, Decimal("0.95")),
            average_basket_value=self._average(basket_values),
            median_basket_value=self._quantile(basket_values, Decimal("0.50")),
            p25_basket_value=self._quantile(basket_values, Decimal("0.25")),
            p75_basket_value=self._quantile(basket_values, Decimal("0.75")),
            p90_basket_value=self._quantile(basket_values, Decimal("0.90")),
            p95_basket_value=self._quantile(basket_values, Decimal("0.95")),
            trend_direction=trend_direction,
            trend_stability=trend_stability,
            trend_change_percent=trend_change_percent,
            volatility_percent=volatility_percent,
            trend_recommendation=self._trend_recommendation(
                trend_direction=trend_direction,
                trend_stability=trend_stability,
                quality_level=quality_level,
            ),
            rolling_points=rolling_points,
            outlier_flags=outlier_flags,
            category_demand_percentiles=category_percentiles,
            product_demand_percentiles=product_percentiles,
            inventory_turnover_readiness=inventory_turnover_readiness,
            insights=insights,
            recommendation=self._recommendation(
                quality_level=quality_level,
                active_sales_day_count=active_sales_day_count,
                basket_count=len(basket_values),
            ),
            source_layer="pos_import_statistics",
        )

    def _payload_occurred_at(self, payload: dict[str, Any]) -> datetime | None:
        occurred_at = payload.get("occurred_at")
        if isinstance(occurred_at, str):
            try:
                parsed = datetime.fromisoformat(occurred_at)
            except ValueError:
                parsed = None
            if parsed is not None:
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=self._time_zone)
                return parsed.astimezone(self._time_zone)

        payload_date = self._parse_payload_date(payload.get("date"))
        if payload_date is None:
            return None
        return datetime.combine(payload_date, time.min, tzinfo=self._time_zone)

    @staticmethod
    def _parse_payload_date(value: Any) -> date | None:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                return None
        return None

    @staticmethod
    def _parse_decimal(value: Any) -> Decimal:
        try:
            return Decimal(str(value or "0"))
        except (InvalidOperation, ValueError):
            return Decimal("0")

    @staticmethod
    def _basket_key(row: ImportRowModel, payload: dict[str, Any]) -> str:
        receipt_no = payload.get("receipt_no")
        if isinstance(receipt_no, str) and receipt_no.strip():
            return receipt_no.strip()
        return str(row.id)

    @staticmethod
    def _payload_label(
        payload: dict[str, Any],
        key: str,
        fallback: str,
    ) -> str:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        return fallback

    @staticmethod
    def _add_demand(
        *,
        daily_quantity: dict[str, dict[date, Decimal]],
        totals: dict[str, dict[str, Decimal | int]],
        label: str,
        business_date: date,
        quantity: Decimal,
        gross_amount: Decimal,
    ) -> None:
        daily_quantity[label][business_date] += quantity
        totals[label]["quantity"] = Decimal(totals[label]["quantity"]) + quantity
        totals[label]["gross_revenue"] = (
            Decimal(totals[label]["gross_revenue"]) + gross_amount
        )
        totals[label]["transaction_count"] = int(totals[label]["transaction_count"]) + 1

    @staticmethod
    def _period_dates(start_date: date, end_date: date) -> list[date]:
        day_count = max((end_date - start_date).days + 1, 1)
        return [
            date.fromordinal(start_date.toordinal() + index)
            for index in range(day_count)
        ]

    def _build_rolling_points(
        self,
        *,
        calendar_dates: list[date],
        daily_revenue: dict[date, Decimal],
        daily_basket_values: dict[date, list[Decimal]],
    ) -> list[DashboardStatisticsTrendPoint]:
        points: list[DashboardStatisticsTrendPoint] = []
        for index, business_date in enumerate(calendar_dates):
            window_dates = calendar_dates[max(index - 6, 0) : index + 1]
            revenue_window = [
                daily_revenue[window_date] for window_date in window_dates
            ]
            daily_baskets = daily_basket_values.get(business_date, [])
            basket_window_values = [
                basket_value
                for window_date in window_dates
                for basket_value in daily_basket_values.get(window_date, [])
            ]
            points.append(
                DashboardStatisticsTrendPoint(
                    business_date=business_date,
                    daily_revenue=daily_revenue[business_date],
                    basket_count=len(daily_baskets),
                    average_basket_value=self._average(daily_baskets),
                    rolling_7_day_average_revenue=self._average(revenue_window),
                    moving_7_day_median_revenue=self._quantile(
                        revenue_window,
                        Decimal("0.50"),
                    ),
                    rolling_7_day_average_basket_value=self._average(
                        basket_window_values,
                    ),
                    moving_7_day_median_basket_value=self._quantile(
                        basket_window_values,
                        Decimal("0.50"),
                    ),
                    source_layer="pos_import_statistics",
                )
            )
        return points

    def _trend_status(
        self,
        *,
        values: list[Decimal],
        active_sales_day_count: int,
    ) -> tuple[str, str, Decimal, Decimal]:
        if active_sales_day_count < 3 or len(values) < 3:
            return "insufficient_data", "low_sample", Decimal("0.00"), Decimal("0.00")

        split_at = max(len(values) // 2, 1)
        first_average = self._average(values[:split_at])
        second_average = self._average(values[split_at:])
        trend_change_percent = self._percent(
            second_average - first_average,
            first_average,
        )
        median = self._quantile(values, Decimal("0.50"))
        volatility_percent = self._percent(
            self._quantile(values, Decimal("0.75"))
            - self._quantile(values, Decimal("0.25")),
            median,
        )

        if volatility_percent >= Decimal("75"):
            return "volatile", "volatile", trend_change_percent, volatility_percent
        if trend_change_percent >= Decimal("10"):
            return "increasing", "stable", trend_change_percent, volatility_percent
        if trend_change_percent <= Decimal("-10"):
            return "decreasing", "stable", trend_change_percent, volatility_percent
        return "flat", "stable", trend_change_percent, volatility_percent

    def _build_outlier_flags(
        self,
        *,
        calendar_dates: list[date],
        daily_revenue: dict[date, Decimal],
        basket_values: list[Decimal],
        quality_level: str,
    ) -> list[DashboardStatisticsOutlierFlag]:
        flags: list[DashboardStatisticsOutlierFlag] = []
        active_revenue = [
            daily_revenue[business_date]
            for business_date in calendar_dates
            if daily_revenue[business_date] > Decimal("0")
        ]
        daily_median = self._quantile(active_revenue, Decimal("0.50"))
        daily_p95 = self._quantile(active_revenue, Decimal("0.95"))
        basket_p95 = self._quantile(basket_values, Decimal("0.95"))

        if daily_median > Decimal("0"):
            for business_date in calendar_dates:
                revenue = daily_revenue[business_date]
                if revenue >= daily_median * Decimal("2.5") and revenue >= daily_p95:
                    flags.append(
                        DashboardStatisticsOutlierFlag(
                            code="unusual_sales_day",
                            severity="warning",
                            label="Szokatlan forgalmu nap",
                            business_date=business_date,
                            metric_value=revenue,
                            baseline_value=daily_median,
                            recommendation=(
                                "Ellenorizd, hogy kampany, event vagy import "
                                "duplikacio okozta-e a kiugrast."
                            ),
                            source_layer="pos_import_statistics",
                        )
                    )

        if basket_p95 > Decimal("0"):
            extreme_baskets = [
                value for value in basket_values if value >= basket_p95 * Decimal("1.5")
            ]
            if extreme_baskets:
                flags.append(
                    DashboardStatisticsOutlierFlag(
                        code="extreme_basket_value",
                        severity="warning",
                        label="Extrem kosarertek",
                        business_date=None,
                        metric_value=max(extreme_baskets),
                        baseline_value=basket_p95,
                        recommendation=(
                            "Nezd meg a nyugtaforrast, mert nagy erteku kosar "
                            "vagy import osszevonas torzithatja az atlagot."
                        ),
                        source_layer="pos_import_statistics",
                    )
                )

        missing_middle_days = [
            business_date
            for business_date in calendar_dates[1:-1]
            if daily_revenue[business_date] == Decimal("0")
            and daily_revenue[date.fromordinal(business_date.toordinal() - 1)]
            > Decimal("0")
            and daily_revenue[date.fromordinal(business_date.toordinal() + 1)]
            > Decimal("0")
        ]
        for business_date in missing_middle_days[:3]:
            flags.append(
                DashboardStatisticsOutlierFlag(
                    code="suspicious_missing_day",
                    severity=(
                        "danger" if quality_level in {"strong", "usable"} else "warning"
                    ),
                    label="Gyanus hianyzo nap",
                    business_date=business_date,
                    metric_value=Decimal("0.00"),
                    baseline_value=daily_median,
                    recommendation=(
                        "Ellenorizd, hogy az adott nap POS exportja nem " "maradt-e ki."
                    ),
                    source_layer="pos_import_statistics",
                )
            )
        return flags[:8]

    def _build_demand_percentiles(
        self,
        *,
        scope: str,
        daily_quantity: dict[str, dict[date, Decimal]],
        totals: dict[str, dict[str, Decimal | int]],
    ) -> list[DashboardDemandPercentileRow]:
        rows: list[DashboardDemandPercentileRow] = []
        for label, quantities_by_date in daily_quantity.items():
            quantities = list(quantities_by_date.values())
            total = totals[label]
            rows.append(
                DashboardDemandPercentileRow(
                    label=label,
                    scope=scope,
                    transaction_count=int(total["transaction_count"]),
                    quantity=Decimal(total["quantity"]),
                    gross_revenue=Decimal(total["gross_revenue"]),
                    median_daily_quantity=self._quantile(quantities, Decimal("0.50")),
                    p90_daily_quantity=self._quantile(quantities, Decimal("0.90")),
                    p95_daily_quantity=self._quantile(quantities, Decimal("0.95")),
                    source_layer="pos_import_demand_percentiles",
                )
            )
        return sorted(
            rows,
            key=lambda row: (row.gross_revenue, row.quantity),
            reverse=True,
        )[:8]

    @staticmethod
    def _inventory_turnover_readiness(
        *,
        pos_row_count: int,
        product_demand_row_count: int,
        category_demand_row_count: int,
        quality_level: str,
    ) -> DashboardInventoryTurnoverReadiness:
        if pos_row_count == 0:
            status = "no_sales_data"
            recommendation = "Keszletforgas elott POS keresleti minta szukseges."
        elif quality_level in {"strong", "usable"} and product_demand_row_count > 0:
            status = "ready_for_turnover_model"
            recommendation = (
                "A keresleti percentilisek keszek; kovetkezo lepes a recept "
                "es inventory movement osszekapcsolasa keszletforgashoz."
            )
        else:
            status = "needs_more_history"
            recommendation = (
                "Keszletforgas alapozhato, de elobb tobb aktiv nap es "
                "stabilabb keresleti minta kell."
            )

        return DashboardInventoryTurnoverReadiness(
            status=status,
            pos_row_count=pos_row_count,
            product_demand_row_count=product_demand_row_count,
            category_demand_row_count=category_demand_row_count,
            required_source_layers=(
                "pos_import_demand_percentiles",
                "production_recipe_read_model",
                "inventory_movement_actual",
            ),
            recommendation=recommendation,
            source_layer="inventory_turnover_readiness",
        )

    def _build_insights(
        self,
        *,
        quality_level: str,
        coverage_percent: Decimal,
        trend_direction: str,
        trend_stability: str,
        trend_change_percent: Decimal,
        volatility_percent: Decimal,
        outlier_flags: tuple[DashboardStatisticsOutlierFlag, ...],
        product_percentiles: tuple[DashboardDemandPercentileRow, ...],
        category_percentiles: tuple[DashboardDemandPercentileRow, ...],
        inventory_turnover_readiness: DashboardInventoryTurnoverReadiness,
    ) -> list[DashboardStatisticsInsight]:
        insights: list[DashboardStatisticsInsight] = []
        confidence = self._insight_confidence(quality_level=quality_level)

        if quality_level in {"limited", "insufficient"}:
            insights.append(
                DashboardStatisticsInsight(
                    code="statistics_sample_gate",
                    severity="warning",
                    category="data_quality",
                    title="A donteshez meg erositeni kell a mintat",
                    summary=(
                        f"A lefedettseg {coverage_percent}%, ezert a forecast es "
                        "ML kovetkeztetes csak ovatos jelzes lehet."
                    ),
                    recommendation=(
                        "Elsokent importlefedettseg, mapping es POS napok "
                        "folytonossaga legyen rendben."
                    ),
                    confidence=confidence,
                    priority_score=Decimal("95"),
                    source_layer="statistics_interpretation",
                )
            )

        danger_flags = [flag for flag in outlier_flags if flag.severity == "danger"]
        warning_flags = [flag for flag in outlier_flags if flag.severity != "danger"]
        if danger_flags or warning_flags:
            flag = danger_flags[0] if danger_flags else warning_flags[0]
            insights.append(
                DashboardStatisticsInsight(
                    code="statistics_outlier_control",
                    severity=flag.severity,
                    category="data_quality",
                    title=flag.label,
                    summary=(
                        "A statisztikai alap torzulhat, mert a POS idosorban "
                        f"{flag.label.lower()} latszik."
                    ),
                    recommendation=flag.recommendation,
                    confidence=confidence,
                    priority_score=(
                        Decimal("90") if flag.severity == "danger" else Decimal("75")
                    ),
                    source_layer="statistics_interpretation",
                )
            )

        if trend_direction in {"increasing", "decreasing"}:
            insights.append(
                DashboardStatisticsInsight(
                    code=f"revenue_trend_{trend_direction}",
                    severity=(
                        "success" if trend_direction == "increasing" else "warning"
                    ),
                    category="trend",
                    title=(
                        "Novekvo beveteli trend"
                        if trend_direction == "increasing"
                        else "Csokkeno beveteli trend"
                    ),
                    summary=(
                        f"A periodus masodik fele {trend_change_percent}% "
                        "elterest mutat az elso felhez kepest."
                    ),
                    recommendation=self._trend_recommendation(
                        trend_direction=trend_direction,
                        trend_stability=trend_stability,
                        quality_level=quality_level,
                    ),
                    confidence=confidence,
                    priority_score=Decimal("70"),
                    source_layer="statistics_interpretation",
                )
            )
        elif trend_stability == "volatile":
            insights.append(
                DashboardStatisticsInsight(
                    code="revenue_volatility",
                    severity="warning",
                    category="trend",
                    title="Ingadozo forgalmi ritmus",
                    summary=(
                        f"A napi bevetel szorodasi jelzese {volatility_percent}%, "
                        "ez keszlet- es munkaerotervezesi kockazat."
                    ),
                    recommendation=(
                        "A kovetkezo forecast szeletben savos, nem pontszeru "
                        "becslesre kell epiteni."
                    ),
                    confidence=confidence,
                    priority_score=Decimal("68"),
                    source_layer="statistics_interpretation",
                )
            )

        if product_percentiles:
            top_product = product_percentiles[0]
            insights.append(
                DashboardStatisticsInsight(
                    code="product_demand_leader",
                    severity="success",
                    category="demand",
                    title="Kiemelt termekkeresleti sav",
                    summary=(
                        f"{top_product.label}: P90 napi kereslet "
                        f"{top_product.p90_daily_quantity} db, P95 "
                        f"{top_product.p95_daily_quantity} db."
                    ),
                    recommendation=(
                        "Ezt a savot hasznald elokeszitesi baseline-kent, majd "
                        "kossuk recepthez es keszletforgashoz."
                    ),
                    confidence=confidence,
                    priority_score=Decimal("62"),
                    source_layer="statistics_interpretation",
                )
            )

        if category_percentiles:
            top_category = category_percentiles[0]
            insights.append(
                DashboardStatisticsInsight(
                    code="category_demand_leader",
                    severity="info",
                    category="demand",
                    title="Vezeto kategoriakereslet",
                    summary=(
                        f"{top_category.label}: P90 napi kereslet "
                        f"{top_category.p90_daily_quantity} db."
                    ),
                    recommendation=(
                        "A kategoria idojaras- es napszak-hatasat a kovetkezo "
                        "forecast/weather modellben erdemes kulon kezelni."
                    ),
                    confidence=confidence,
                    priority_score=Decimal("50"),
                    source_layer="statistics_interpretation",
                )
            )

        if inventory_turnover_readiness.status == "ready_for_turnover_model":
            insights.append(
                DashboardStatisticsInsight(
                    code="inventory_turnover_ready",
                    severity="success",
                    category="inventory",
                    title="Keszletforgas modell indithato",
                    summary=(
                        "A POS keresleti percentilisek mar eleg erosek ahhoz, "
                        "hogy recept es inventory actual reteggel osszekossuk."
                    ),
                    recommendation=inventory_turnover_readiness.recommendation,
                    confidence=confidence,
                    priority_score=Decimal("58"),
                    source_layer="statistics_interpretation",
                )
            )

        return sorted(
            insights,
            key=lambda insight: insight.priority_score,
            reverse=True,
        )[:5]

    @staticmethod
    def _average(values: list[Decimal]) -> Decimal:
        if not values:
            return Decimal("0")
        return (sum(values, Decimal("0")) / Decimal(len(values))).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @staticmethod
    def _quantile(values: list[Decimal], quantile: Decimal) -> Decimal:
        if not values:
            return Decimal("0")
        ordered = sorted(values)
        if len(ordered) == 1:
            return ordered[0].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        position = int(
            (
                (Decimal(len(ordered) - 1) * quantile).to_integral_value(
                    rounding=ROUND_HALF_UP,
                )
            )
        )
        return ordered[position].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _percent(numerator: Decimal, denominator: Decimal) -> Decimal:
        if denominator <= Decimal("0"):
            return Decimal("0")
        return (numerator / denominator * Decimal("100")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @staticmethod
    def _quality_level(
        *,
        active_sales_day_count: int,
        basket_count: int,
        coverage_percent: Decimal,
    ) -> str:
        if (
            active_sales_day_count >= 21
            and basket_count >= 300
            and coverage_percent >= 70
        ):
            return "strong"
        if (
            active_sales_day_count >= 10
            and basket_count >= 100
            and coverage_percent >= 40
        ):
            return "usable"
        if active_sales_day_count >= 3 and basket_count >= 20:
            return "limited"
        return "insufficient"

    @staticmethod
    def _insight_confidence(*, quality_level: str) -> str:
        if quality_level == "strong":
            return "high"
        if quality_level == "usable":
            return "medium"
        if quality_level == "limited":
            return "low"
        return "very_low"

    @staticmethod
    def _trend_recommendation(
        *,
        trend_direction: str,
        trend_stability: str,
        quality_level: str,
    ) -> str:
        if quality_level in {"limited", "insufficient"}:
            return (
                "A trend csak ovatos jelzes: elobb tobb aktiv nap es stabilabb "
                "importlefedettseg kell."
            )
        if trend_stability == "volatile":
            return (
                "A forgalom erosen ingadozik; forecast elott outlier es import "
                "ellenorzes javasolt."
            )
        if trend_direction == "increasing":
            return (
                "Emelkedo trend latszik; a kovetkezo keszlet- es elokeszitesi "
                "donteseknel a P90/P95 keresleti savot is erdemes figyelni."
            )
        if trend_direction == "decreasing":
            return (
                "Csokkeno trend latszik; keszletfelhalmozas helyett ovatosabb "
                "beszerzesi baseline javasolt."
            )
        return (
            "Stabil trend mellett a median es rolling atlag jo baseline "
            "elokeszitesi alap."
        )

    @staticmethod
    def _recommendation(
        *,
        quality_level: str,
        active_sales_day_count: int,
        basket_count: int,
    ) -> str:
        if quality_level == "strong":
            return (
                "Stabil statisztikai alap: median, percentilis es baseline "
                "forecast dontestamogatasra hasznalhato."
            )
        if quality_level == "usable":
            return (
                "Hasznalhato statisztikai alap: baseline forecast indithato, "
                "de confidence jeloles kotelezo."
            )
        if quality_level == "limited":
            return (
                "Korlatozott minta: leiro statisztikara alkalmas, "
                "kovetkezteteshez es forecasthez ovatosan hasznalhato."
            )
        return (
            "Nincs eleg tiszta historikus minta. Elobb import, mapping, AFA es "
            "forgalmi lefedettseg szukseges."
        )
