"""Build event analyzer summary read model."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from app.modules.events.domain.entities.event import Event
from app.modules.events.domain.entities.event_analytics_summary import (
    EventAnalyticsHighlight,
    EventAnalyticsHighlights,
    EventAnalyticsInsight,
    EventAnalyticsMetrics,
    EventAnalyticsSummary,
    EventPerformerAnalyticsRow,
)
from app.modules.events.domain.entities.event_performance import EventPerformance
from app.modules.events.domain.repositories.event_repository import EventRepository
from app.modules.events.infrastructure.repositories.sqlalchemy_event_performance_repository import (
    SqlAlchemyEventPerformanceRepository,
)

MONEY_QUANT = Decimal("0.01")
PERCENT_QUANT = Decimal("0.01")
UNKNOWN_EVENT_TITLE = "Ismeretlen esemény"
UNKNOWN_PERFORMER = "Fellépő nélkül"


class GetEventAnalyticsSummaryQuery:
    """Return the aggregate business read model for the event analyzer."""

    def __init__(
        self,
        *,
        event_repository: EventRepository,
        performance_repository: SqlAlchemyEventPerformanceRepository,
    ) -> None:
        self.event_repository = event_repository
        self.performance_repository = performance_repository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        status: str | None = None,
        is_active: bool | None = None,
        starts_from: datetime | None = None,
        starts_to: datetime | None = None,
        limit: int = 200,
    ) -> EventAnalyticsSummary:
        normalized_status = None if status in {None, "", "all"} else status
        events = self.event_repository.list_many(
            business_unit_id=business_unit_id,
            status=normalized_status,
            is_active=is_active,
            starts_from=starts_from,
            starts_to=starts_to,
            limit=limit,
        )
        performances = self.performance_repository.list_many(
            business_unit_id=business_unit_id,
            status=normalized_status,
            is_active=is_active,
            starts_from=starts_from,
            starts_to=starts_to,
            limit=limit,
        )
        event_by_id = {event.id: event for event in events}
        return EventAnalyticsSummary(
            metrics=self._build_metrics(performances),
            highlights=self._build_highlights(performances, event_by_id),
            performer_rows=tuple(self._build_performer_rows(performances, event_by_id)),
            insights=tuple(self._build_insights(performances, event_by_id)),
        )

    def _build_metrics(self, performances: list[EventPerformance]) -> EventAnalyticsMetrics:
        ticket_actual_count = sum(
            1 for performance in performances if performance.ticket_revenue_source == "ticket_actual"
        )
        missing_ticket_actual_count = len(performances) - ticket_actual_count
        return EventAnalyticsMetrics(
            event_count=len(performances),
            ticket_revenue_gross=self._money(
                sum((performance.ticket_revenue_gross for performance in performances), Decimal("0"))
            ),
            bar_revenue_gross=self._money(
                sum((performance.bar_revenue_gross for performance in performances), Decimal("0"))
            ),
            own_revenue=self._money(
                sum((performance.own_revenue for performance in performances), Decimal("0"))
            ),
            event_profit_lite=self._money(
                sum((performance.event_profit_lite for performance in performances), Decimal("0"))
            ),
            receipt_count=sum(performance.receipt_count for performance in performances),
            ticket_actual_count=ticket_actual_count,
            missing_ticket_actual_count=missing_ticket_actual_count,
            ticket_actual_coverage_percent=self._ratio_percent(
                Decimal(ticket_actual_count),
                Decimal(len(performances)),
            )
            or Decimal("0.00"),
            profitable_count=sum(1 for performance in performances if performance.profit_status == "profitable"),
            loss_count=sum(1 for performance in performances if performance.profit_status == "loss"),
        )

    def _build_highlights(
        self,
        performances: list[EventPerformance],
        event_by_id: dict[uuid.UUID, Event],
    ) -> EventAnalyticsHighlights:
        top_profit = self._first_sorted(
            performances,
            key=lambda performance: performance.event_profit_lite,
        )
        most_popular = self._first_sorted(
            performances,
            key=lambda performance: (Decimal(performance.receipt_count), Decimal(performance.source_row_count)),
        )
        highest_revenue = self._first_sorted(
            performances,
            key=lambda performance: performance.total_revenue_gross,
        )
        top_margin = self._first_sorted(
            [performance for performance in performances if performance.event_profit_margin_percent is not None],
            key=lambda performance: performance.event_profit_margin_percent or Decimal("0"),
        )
        highest_cost_ratio = self._first_sorted(
            [performance for performance in performances if performance.operating_cost_ratio_percent is not None],
            key=lambda performance: performance.operating_cost_ratio_percent or Decimal("0"),
        )
        return EventAnalyticsHighlights(
            top_profit=self._highlight(top_profit, event_by_id, "event_profit_lite"),
            most_popular=self._highlight(most_popular, event_by_id, "receipt_count"),
            highest_revenue=self._highlight(highest_revenue, event_by_id, "total_revenue_gross"),
            top_margin=self._highlight(top_margin, event_by_id, "event_profit_margin_percent"),
            highest_cost_ratio=self._highlight(
                highest_cost_ratio,
                event_by_id,
                "operating_cost_ratio_percent",
            ),
        )

    def _build_performer_rows(
        self,
        performances: list[EventPerformance],
        event_by_id: dict[uuid.UUID, Event],
    ) -> list[EventPerformerAnalyticsRow]:
        performer_totals: dict[str, dict[str, Decimal | int]] = defaultdict(
            lambda: {
                "event_count": 0,
                "ticket_revenue_gross": Decimal("0"),
                "bar_revenue_gross": Decimal("0"),
                "own_revenue": Decimal("0"),
                "event_profit_lite": Decimal("0"),
            }
        )
        for performance in performances:
            event = event_by_id.get(performance.event_id)
            if event and event.status == "cancelled":
                continue
            performer = event.performer_name if event and event.performer_name else UNKNOWN_PERFORMER
            current = performer_totals[performer]
            current["event_count"] = int(current["event_count"]) + 1
            current["ticket_revenue_gross"] = Decimal(current["ticket_revenue_gross"]) + performance.ticket_revenue_gross
            current["bar_revenue_gross"] = Decimal(current["bar_revenue_gross"]) + performance.bar_revenue_gross
            current["own_revenue"] = Decimal(current["own_revenue"]) + performance.own_revenue
            current["event_profit_lite"] = Decimal(current["event_profit_lite"]) + performance.event_profit_lite

        rows = [
            EventPerformerAnalyticsRow(
                performer=performer,
                event_count=int(values["event_count"]),
                ticket_revenue_gross=self._money(Decimal(values["ticket_revenue_gross"])),
                bar_revenue_gross=self._money(Decimal(values["bar_revenue_gross"])),
                own_revenue=self._money(Decimal(values["own_revenue"])),
                event_profit_lite=self._money(Decimal(values["event_profit_lite"])),
            )
            for performer, values in performer_totals.items()
        ]
        return sorted(rows, key=lambda row: row.event_profit_lite, reverse=True)

    def _build_insights(
        self,
        performances: list[EventPerformance],
        event_by_id: dict[uuid.UUID, Event],
    ) -> list[EventAnalyticsInsight]:
        insights: list[EventAnalyticsInsight] = []
        missing_ticket_rows = sorted(
            [
                performance
                for performance in performances
                if performance.ticket_revenue_source != "ticket_actual"
            ],
            key=lambda performance: performance.starts_at,
            reverse=True,
        )
        if missing_ticket_rows:
            performance = missing_ticket_rows[0]
            insights.append(
                EventAnalyticsInsight(
                    key="ticket-actual-missing",
                    tone="warning",
                    title="Ticket actual hiányzik",
                    event_id=performance.event_id,
                    event_title=self._event_title(performance, event_by_id),
                    metric=f"{len(missing_ticket_rows)} event",
                    detail="Jegybevétel csak külön ticket actualból számolódik, POS-ból nem.",
                )
            )

        top_profit = self._first_sorted(performances, key=lambda performance: performance.event_profit_lite)
        if top_profit is not None:
            insights.append(
                EventAnalyticsInsight(
                    key="top-profit",
                    tone="success",
                    title="Legjobb üzleti eredmény",
                    event_id=top_profit.event_id,
                    event_title=self._event_title(top_profit, event_by_id),
                    metric=self._format_money(top_profit.event_profit_lite),
                    detail=(
                        f"{self._profit_status_label(top_profit.profit_status)} · "
                        f"margin {self._format_percent(top_profit.event_profit_margin_percent)}"
                    ),
                )
            )

        highest_cost_ratio = self._first_sorted(
            [performance for performance in performances if performance.operating_cost_ratio_percent is not None],
            key=lambda performance: performance.operating_cost_ratio_percent or Decimal("0"),
        )
        if highest_cost_ratio is not None:
            cost_ratio = highest_cost_ratio.operating_cost_ratio_percent or Decimal("0")
            insights.append(
                EventAnalyticsInsight(
                    key="cost-risk",
                    tone="danger" if cost_ratio >= Decimal("50") else "warning" if cost_ratio >= Decimal("30") else "neutral",
                    title="Magas költségarány" if cost_ratio >= Decimal("50") else "Költségfigyelő",
                    event_id=highest_cost_ratio.event_id,
                    event_title=self._event_title(highest_cost_ratio, event_by_id),
                    metric=self._format_percent(highest_cost_ratio.operating_cost_ratio_percent),
                    detail=(
                        f"Profit {self._format_money(highest_cost_ratio.event_profit_lite)} · "
                        f"margin {self._format_percent(highest_cost_ratio.event_profit_margin_percent)}"
                    ),
                )
            )

        popular_weak_margin = self._first_sorted(
            [
                performance
                for performance in performances
                if performance.receipt_count > 0
                and (
                    performance.profit_status == "loss"
                    or (
                        performance.event_profit_margin_percent is not None
                        and performance.event_profit_margin_percent < Decimal("20")
                    )
                )
            ],
            key=lambda performance: Decimal(performance.receipt_count),
        )
        if popular_weak_margin is not None:
            insights.append(
                EventAnalyticsInsight(
                    key="popular-weak-margin",
                    tone="danger" if popular_weak_margin.profit_status == "loss" else "warning",
                    title="Népszerű, de gyenge margin",
                    event_id=popular_weak_margin.event_id,
                    event_title=self._event_title(popular_weak_margin, event_by_id),
                    metric=f"{popular_weak_margin.receipt_count} nyugta",
                    detail=(
                        f"Margin {self._format_percent(popular_weak_margin.event_profit_margin_percent)} · "
                        f"profit {self._format_money(popular_weak_margin.event_profit_lite)}"
                    ),
                )
            )

        strongest_bar_mix = self._first_sorted(
            [
                performance
                for performance in performances
                if performance.bar_revenue_share_percent is not None
            ],
            key=lambda performance: performance.bar_revenue_share_percent or Decimal("0"),
        )
        if strongest_bar_mix is not None and (
            strongest_bar_mix.bar_revenue_share_percent or Decimal("0")
        ) >= Decimal("50"):
            insights.append(
                EventAnalyticsInsight(
                    key="bar-mix",
                    tone="neutral",
                    title="Bárvezérelt event",
                    event_id=strongest_bar_mix.event_id,
                    event_title=self._event_title(strongest_bar_mix, event_by_id),
                    metric=self._format_percent(strongest_bar_mix.bar_revenue_share_percent),
                    detail=(
                        f"Bárbevétel {self._format_money(strongest_bar_mix.bar_revenue_gross)} · "
                        f"jegy {self._format_percent(strongest_bar_mix.ticket_revenue_share_percent)}"
                    ),
                )
            )

        return insights[:4]

    @staticmethod
    def _first_sorted(
        performances: list[EventPerformance],
        *,
        key: object,
    ) -> EventPerformance | None:
        if not performances:
            return None
        return sorted(performances, key=key, reverse=True)[0]  # type: ignore[arg-type]

    @staticmethod
    def _highlight(
        performance: EventPerformance | None,
        event_by_id: dict[uuid.UUID, Event],
        metric_name: str,
    ) -> EventAnalyticsHighlight:
        if performance is None:
            return EventAnalyticsHighlight(
                event_id=None,
                title=None,
                performer_name=None,
                starts_at=None,
                metric_value=None,
            )
        event = event_by_id.get(performance.event_id)
        metric = getattr(performance, metric_name)
        return EventAnalyticsHighlight(
            event_id=performance.event_id,
            title=event.title if event else UNKNOWN_EVENT_TITLE,
            performer_name=event.performer_name if event else None,
            starts_at=performance.starts_at,
            metric_value=Decimal(metric) if metric is not None else None,
        )

    @staticmethod
    def _event_title(
        performance: EventPerformance,
        event_by_id: dict[uuid.UUID, Event],
    ) -> str:
        return event_by_id.get(performance.event_id).title if performance.event_id in event_by_id else UNKNOWN_EVENT_TITLE

    @staticmethod
    def _profit_status_label(value: str) -> str:
        return {
            "profitable": "Nyereséges",
            "break_even": "Nullszaldó",
            "loss": "Veszteséges",
            "no_revenue": "Nincs bevétel",
        }.get(value, value)

    @staticmethod
    def _ratio_percent(numerator: Decimal, denominator: Decimal) -> Decimal | None:
        if denominator <= 0:
            return None
        return (numerator * Decimal("100") / denominator).quantize(
            PERCENT_QUANT,
            rounding=ROUND_HALF_UP,
        )

    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(MONEY_QUANT)

    @staticmethod
    def _format_money(value: Decimal) -> str:
        rounded = value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return f"{rounded:,.0f} Ft".replace(",", " ")

    @staticmethod
    def _format_percent(value: Decimal | None) -> str:
        if value is None:
            return "-"
        return f"{value.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}%"
