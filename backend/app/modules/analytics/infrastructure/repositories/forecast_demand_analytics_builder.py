"""Forecast demand read-model orchestration from POS and weather history."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo

from app.modules.analytics.domain.entities.dashboard_snapshot import (
    DashboardForecastCategoryDemandRow,
    DashboardForecastImpactRow,
    DashboardForecastPeakTimeRow,
    DashboardForecastProductDemandRow,
)
from app.modules.analytics.infrastructure.repositories.forecast_analytics_reader import (
    ForecastAnalyticsReader,
    time_window_hours,
    time_window_label,
)
from app.modules.analytics.infrastructure.repositories.forecast_demand_rules import (
    average_decimal,
    average_revenue_by_key,
    average_sales_by_key,
    average_window_sales_by_key,
    category_recommendation,
    demand_signal,
    dominant_label,
    dominant_product_categories,
    impact_recommendation,
    peak_time_recommendation,
    product_recommendation,
)
from app.modules.analytics.infrastructure.repositories.weather_analytics_reader import (
    WeatherAnalyticsReader,
    hour_start_utc,
    temperature_band,
    weather_condition_band,
)
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel


class ForecastDemandAnalyticsBuilder:
    """Build demand forecasts while keeping SQLAlchemy orchestration outside."""

    def __init__(
        self,
        *,
        forecast_reader: ForecastAnalyticsReader,
        weather_reader: WeatherAnalyticsReader,
        time_zone: ZoneInfo,
        unknown_category: str,
        unknown_product: str,
        horizon_days: int,
    ) -> None:
        self._forecast_reader = forecast_reader
        self._weather_reader = weather_reader
        self._time_zone = time_zone
        self._unknown_category = unknown_category
        self._unknown_product = unknown_product
        self._horizon_days = horizon_days

    def build_impact(
        self,
        *,
        rows: list[ImportRowModel],
        scope: str,
    ) -> list[DashboardForecastImpactRow]:
        forecasts = self._upcoming_forecasts()
        historical_days = self._historical_sales_days(rows)
        if not forecasts or not historical_days:
            return []

        exact = average_revenue_by_key(
            historical_days,
            key_builder=lambda row: (
                row["temperature_band"],
                row["condition_band"],
            ),
        )
        weekdays = average_revenue_by_key(
            historical_days,
            key_builder=lambda row: row["weekday"],
        )
        overall = average_decimal(
            [Decimal(row["revenue"]) for row in historical_days]
        )
        insights: list[DashboardForecastImpactRow] = []
        for forecast_date, values in sorted(
            self._forecast_reader.aggregate_days(forecasts).items()
        ):
            forecast_hours = int(values["hour_count"])
            if forecast_hours <= 0:
                continue
            temperature_average, band, condition = self._forecast_context(values)
            if (band, condition) in exact:
                expected = exact[(band, condition)]
                confidence = "magas"
            elif forecast_date.weekday() in weekdays:
                expected = weekdays[forecast_date.weekday()]
                confidence = "kozepes"
            else:
                expected = overall or Decimal("0")
                confidence = "alacsony"
            historical_average = (
                overall if overall is not None and overall > Decimal("0") else expected
            )
            insights.append(
                DashboardForecastImpactRow(
                    forecast_date=forecast_date,
                    forecast_hours=forecast_hours,
                    dominant_temperature_band=band,
                    dominant_condition_band=condition,
                    average_temperature_c=temperature_average,
                    precipitation_mm=Decimal(values["precipitation_sum"]),
                    expected_revenue=expected,
                    historical_average_revenue=historical_average,
                    confidence=confidence,
                    recommendation=impact_recommendation(
                        scope=scope,
                        temperature_band=band,
                        condition_band=condition,
                        expected_revenue=expected,
                        historical_average=historical_average,
                    ),
                    forecast_updated_at=values["latest_forecast_run_at"],
                    source_layer="weather_forecast_cache",
                )
            )
        return insights[: self._horizon_days]

    def build_category_demand(
        self,
        *,
        rows: list[ImportRowModel],
        scope: str,
    ) -> list[DashboardForecastCategoryDemandRow]:
        if scope == "flow":
            return []
        forecasts = self._upcoming_forecasts()
        historical = self._historical_dimension_days(
            rows,
            dimension_name="category_name",
            fallback=self._unknown_category,
        )
        if not forecasts or not historical:
            return []

        exact = average_sales_by_key(
            historical,
            key_builder=lambda row: (
                row["category_name"],
                row["temperature_band"],
                row["condition_band"],
            ),
        )
        weekdays = average_sales_by_key(
            historical,
            key_builder=lambda row: (row["category_name"], row["weekday"]),
        )
        category_average = average_sales_by_key(
            historical,
            key_builder=lambda row: row["category_name"],
        )

        rows_by_date: dict[date, list[DashboardForecastCategoryDemandRow]] = defaultdict(
            list
        )
        for forecast_date, values in sorted(
            self._forecast_reader.aggregate_days(forecasts).items()
        ):
            _, band, condition = self._forecast_context(values)
            for category_name, average in category_average.items():
                baseline, confidence = self._select_baseline(
                    exact=exact,
                    exact_key=(category_name, band, condition),
                    weekdays=weekdays,
                    weekday_key=(category_name, forecast_date.weekday()),
                    fallback=average,
                )
                expected_revenue = Decimal(baseline["revenue"])
                historical_average = Decimal(average["revenue"])
                uplift = self._uplift(expected_revenue, historical_average)
                signal = demand_signal(uplift)
                rows_by_date[forecast_date].append(
                    DashboardForecastCategoryDemandRow(
                        forecast_date=forecast_date,
                        category_name=str(category_name),
                        dominant_temperature_band=band,
                        dominant_condition_band=condition,
                        expected_revenue=expected_revenue,
                        expected_quantity=Decimal(baseline["quantity"]),
                        historical_average_revenue=historical_average,
                        revenue_uplift_percent=uplift,
                        confidence=confidence,
                        demand_signal=signal,
                        recommendation=category_recommendation(
                            category_name=str(category_name),
                            temperature_band=band,
                            condition_band=condition,
                            signal=signal,
                        ),
                        source_layer="weather_forecast_category_model",
                    )
                )
        return self._rank_by_date(rows_by_date, per_day=3, total=18)

    def build_product_demand(
        self,
        *,
        rows: list[ImportRowModel],
        scope: str,
    ) -> list[DashboardForecastProductDemandRow]:
        if scope == "flow":
            return []
        forecasts = self._upcoming_forecasts()
        historical = self._historical_dimension_days(
            rows,
            dimension_name="product_name",
            fallback=self._unknown_product,
            include_category=True,
        )
        if not forecasts or not historical:
            return []

        exact = average_sales_by_key(
            historical,
            key_builder=lambda row: (
                row["product_name"],
                row["temperature_band"],
                row["condition_band"],
            ),
        )
        weekdays = average_sales_by_key(
            historical,
            key_builder=lambda row: (row["product_name"], row["weekday"]),
        )
        product_average = average_sales_by_key(
            historical,
            key_builder=lambda row: row["product_name"],
        )
        categories = dominant_product_categories(
            historical,
            fallback=self._unknown_category,
        )

        rows_by_date: dict[date, list[DashboardForecastProductDemandRow]] = defaultdict(
            list
        )
        for forecast_date, values in sorted(
            self._forecast_reader.aggregate_days(forecasts).items()
        ):
            _, band, condition = self._forecast_context(values)
            for product_name, average in product_average.items():
                baseline, confidence = self._select_baseline(
                    exact=exact,
                    exact_key=(product_name, band, condition),
                    weekdays=weekdays,
                    weekday_key=(product_name, forecast_date.weekday()),
                    fallback=average,
                )
                expected_revenue = Decimal(baseline["revenue"])
                historical_average = Decimal(average["revenue"])
                uplift = self._uplift(expected_revenue, historical_average)
                signal = demand_signal(uplift)
                rows_by_date[forecast_date].append(
                    DashboardForecastProductDemandRow(
                        forecast_date=forecast_date,
                        product_name=str(product_name),
                        category_name=categories.get(
                            str(product_name),
                            self._unknown_category,
                        ),
                        dominant_temperature_band=band,
                        dominant_condition_band=condition,
                        expected_revenue=expected_revenue,
                        expected_quantity=Decimal(baseline["quantity"]),
                        historical_average_revenue=historical_average,
                        revenue_uplift_percent=uplift,
                        confidence=confidence,
                        demand_signal=signal,
                        recommendation=product_recommendation(
                            product_name=str(product_name),
                            signal=signal,
                            condition_band=condition,
                        ),
                        source_layer="weather_forecast_product_model",
                    )
                )
        return self._rank_by_date(rows_by_date, per_day=5, total=30)

    def build_peak_times(
        self,
        *,
        rows: list[ImportRowModel],
        scope: str,
    ) -> list[DashboardForecastPeakTimeRow]:
        if scope == "flow":
            return []
        forecasts = self._upcoming_forecasts()
        historical = self._historical_time_windows(rows)
        if not forecasts or not historical:
            return []

        exact = average_window_sales_by_key(
            historical,
            key_builder=lambda row: (
                row["time_window"],
                row["temperature_band"],
                row["condition_band"],
            ),
        )
        weekdays = average_window_sales_by_key(
            historical,
            key_builder=lambda row: (row["time_window"], row["weekday"]),
        )
        window_average = average_window_sales_by_key(
            historical,
            key_builder=lambda row: row["time_window"],
        )
        rows_by_date: dict[date, list[DashboardForecastPeakTimeRow]] = defaultdict(
            list
        )
        for (forecast_date, window), values in sorted(
            self._forecast_reader.aggregate_time_windows(forecasts).items()
        ):
            _, band, condition = self._forecast_context(values)
            exact_key = (window, band, condition)
            weekday_key = (window, forecast_date.weekday())
            if exact_key in exact:
                baseline, confidence = exact[exact_key], "magas"
            elif weekday_key in weekdays:
                baseline, confidence = weekdays[weekday_key], "kozepes"
            elif window in window_average:
                baseline, confidence = window_average[window], "alacsony"
            else:
                continue
            average = window_average.get(window, baseline)
            expected = Decimal(baseline["revenue"])
            historical_average = Decimal(average["revenue"])
            uplift = self._uplift(expected, historical_average)
            signal = demand_signal(uplift)
            start_hour, end_hour = time_window_hours(str(window))
            rows_by_date[forecast_date].append(
                DashboardForecastPeakTimeRow(
                    forecast_date=forecast_date,
                    time_window=str(window),
                    start_hour=start_hour,
                    end_hour=end_hour,
                    dominant_temperature_band=band,
                    dominant_condition_band=condition,
                    expected_revenue=expected,
                    expected_quantity=Decimal(baseline["quantity"]),
                    expected_transaction_count=int(
                        Decimal(baseline["transaction_count"]).to_integral_value()
                    ),
                    historical_average_revenue=historical_average,
                    revenue_uplift_percent=uplift,
                    confidence=confidence,
                    demand_signal=signal,
                    recommendation=peak_time_recommendation(
                        time_window=str(window),
                        signal=signal,
                    ),
                    source_layer="weather_forecast_peak_time_model",
                )
            )
        ranked: list[DashboardForecastPeakTimeRow] = []
        for forecast_date in sorted(rows_by_date):
            ranked.extend(
                sorted(
                    rows_by_date[forecast_date],
                    key=lambda row: (
                        row.expected_revenue,
                        row.expected_transaction_count,
                    ),
                    reverse=True,
                )[:2]
            )
        return ranked[:14]

    def _upcoming_forecasts(self) -> list[Any]:
        now = datetime.now(self._time_zone)
        return self._forecast_reader.list_forecasts(
            start_at=now,
            end_at=now + timedelta(days=self._horizon_days),
        )

    def _historical_sales_days(
        self,
        rows: list[ImportRowModel],
    ) -> list[dict[str, object]]:
        matched = self._weather_matched_rows(rows)
        daily: dict[date, dict[str, Any]] = defaultdict(
            lambda: {
                "revenue": Decimal("0"),
                "temperatures": [],
                "condition_counts": defaultdict(int),
            }
        )
        for row, payload, occurred_at, observation in matched:
            local_date = occurred_at.astimezone(self._time_zone).date()
            daily[local_date]["revenue"] += self._parse_decimal(
                payload.get("gross_amount")
            )
            self._add_weather_context(daily[local_date], observation)
        return [
            self._historical_row(local_date, values)
            for local_date, values in daily.items()
        ]

    def _historical_dimension_days(
        self,
        rows: list[ImportRowModel],
        *,
        dimension_name: str,
        fallback: str,
        include_category: bool = False,
    ) -> list[dict[str, object]]:
        daily: dict[tuple[date, str], dict[str, Any]] = defaultdict(
            lambda: {
                "revenue": Decimal("0"),
                "quantity": Decimal("0"),
                "temperatures": [],
                "condition_counts": defaultdict(int),
                "category_counts": defaultdict(int),
            }
        )
        for _row, payload, occurred_at, observation in self._weather_matched_rows(
            rows
        ):
            dimension = self._extract_text(payload.get(dimension_name), fallback=fallback)
            local_date = occurred_at.astimezone(self._time_zone).date()
            values = daily[(local_date, dimension)]
            values["revenue"] += self._parse_decimal(payload.get("gross_amount"))
            values["quantity"] += self._parse_decimal(payload.get("quantity"))
            if include_category:
                values["category_counts"][
                    self._extract_text(
                        payload.get("category_name"),
                        fallback=self._unknown_category,
                    )
                ] += 1
            self._add_weather_context(values, observation)

        result: list[dict[str, object]] = []
        for (local_date, dimension), values in daily.items():
            item = self._historical_row(local_date, values)
            item[dimension_name] = dimension
            item["quantity"] = Decimal(values["quantity"])
            if include_category:
                item["category_name"] = dominant_label(
                    values["category_counts"],
                    fallback=self._unknown_category,
                )
            result.append(item)
        return result

    def _historical_time_windows(
        self,
        rows: list[ImportRowModel],
    ) -> list[dict[str, object]]:
        windows: dict[tuple[date, str], dict[str, Any]] = defaultdict(
            lambda: {
                "revenue": Decimal("0"),
                "quantity": Decimal("0"),
                "receipt_keys": set(),
                "temperatures": [],
                "condition_counts": defaultdict(int),
            }
        )
        for row, payload, occurred_at, observation in self._weather_matched_rows(
            rows
        ):
            local_value = occurred_at.astimezone(self._time_zone)
            window = time_window_label(local_value.hour)
            values = windows[(local_value.date(), window)]
            values["revenue"] += self._parse_decimal(payload.get("gross_amount"))
            values["quantity"] += self._parse_decimal(payload.get("quantity"))
            values["receipt_keys"].add(
                self._extract_optional_text(payload.get("receipt_no")) or str(row.id)
            )
            self._add_weather_context(values, observation)
        result: list[dict[str, object]] = []
        for (local_date, window), values in windows.items():
            item = self._historical_row(local_date, values)
            item.update(
                {
                    "time_window": window,
                    "quantity": Decimal(values["quantity"]),
                    "transaction_count": Decimal(len(values["receipt_keys"])),
                }
            )
            result.append(item)
        return result

    def _weather_matched_rows(
        self,
        rows: list[ImportRowModel],
    ) -> list[tuple[ImportRowModel, dict[str, Any], datetime, Any]]:
        occurred = [
            value
            for row in rows
            if (
                value := self._payload_occurred_at(row.normalized_payload or {})
            )
            is not None
        ]
        if not occurred:
            return []
        observations = self._weather_reader.list_observations(
            start_at=min(occurred),
            end_at=max(occurred) + timedelta(hours=1),
        )
        by_hour = {
            hour_start_utc(observation.observed_at): observation
            for observation in observations
        }
        result = []
        for row in rows:
            payload = row.normalized_payload or {}
            occurred_at = self._payload_occurred_at(payload)
            if occurred_at is None:
                continue
            observation = by_hour.get(hour_start_utc(occurred_at))
            if observation is not None:
                result.append((row, payload, occurred_at, observation))
        return result

    def _historical_row(
        self,
        local_date: date,
        values: dict[str, Any],
    ) -> dict[str, object]:
        average_temperature = average_decimal(values["temperatures"])
        return {
            "date": local_date,
            "weekday": local_date.weekday(),
            "revenue": Decimal(values["revenue"]),
            "temperature_band": (
                temperature_band(average_temperature)
                if average_temperature is not None
                else "ismeretlen"
            ),
            "condition_band": dominant_label(
                values["condition_counts"],
                fallback="ismeretlen",
            ),
        }

    @staticmethod
    def _add_weather_context(values: dict[str, Any], observation: Any) -> None:
        if observation.temperature_c is not None:
            values["temperatures"].append(Decimal(observation.temperature_c))
        values["condition_counts"][weather_condition_band(observation)] += 1

    @staticmethod
    def _select_baseline(
        *,
        exact: dict[Any, dict[str, Decimal]],
        exact_key: Any,
        weekdays: dict[Any, dict[str, Decimal]],
        weekday_key: Any,
        fallback: dict[str, Decimal],
    ) -> tuple[dict[str, Decimal], str]:
        if exact_key in exact:
            return exact[exact_key], "magas"
        if weekday_key in weekdays:
            return weekdays[weekday_key], "kozepes"
        return fallback, "alacsony"

    @staticmethod
    def _forecast_context(values: dict[str, Any]) -> tuple[Decimal | None, str, str]:
        temperature_average = average_decimal(
            [Decimal(value) for value in values["temperatures"]]
        )
        return (
            temperature_average,
            (
                temperature_band(temperature_average)
                if temperature_average is not None
                else "ismeretlen"
            ),
            dominant_label(values["condition_counts"], fallback="ismeretlen"),
        )

    @staticmethod
    def _uplift(expected: Decimal, historical: Decimal) -> Decimal:
        if historical <= Decimal("0"):
            return Decimal("0")
        return (expected - historical) / historical * Decimal("100")

    @staticmethod
    def _rank_by_date(
        rows_by_date: dict[date, list[Any]],
        *,
        per_day: int,
        total: int,
    ) -> list[Any]:
        result: list[Any] = []
        for forecast_date in sorted(rows_by_date):
            result.extend(
                sorted(
                    rows_by_date[forecast_date],
                    key=lambda row: (row.expected_revenue, row.expected_quantity),
                    reverse=True,
                )[:per_day]
            )
        return result[:total]

    def _payload_occurred_at(self, payload: dict[str, Any]) -> datetime | None:
        value = payload.get("occurred_at")
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value)
            except ValueError:
                parsed = None
            if parsed is not None:
                return (
                    parsed.replace(tzinfo=self._time_zone)
                    if parsed.tzinfo is None
                    else parsed.astimezone(self._time_zone)
                )
        value = payload.get("date")
        if not isinstance(value, str):
            return None
        try:
            parsed_date = date.fromisoformat(value)
        except ValueError:
            return None
        return datetime(
            parsed_date.year,
            parsed_date.month,
            parsed_date.day,
            tzinfo=self._time_zone,
        )

    @staticmethod
    def _parse_decimal(value: Any) -> Decimal:
        if value is None:
            return Decimal("0")
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return Decimal("0")

    @staticmethod
    def _extract_text(value: Any, *, fallback: str) -> str:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return fallback

    @staticmethod
    def _extract_optional_text(value: Any) -> str | None:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None
