"""Inventory variance action suggestion query."""

from __future__ import annotations

import uuid
from decimal import Decimal

from app.modules.inventory.domain.entities.inventory_item import (
    InventoryVarianceActionReview,
    InventoryVarianceActionSuggestion,
    InventoryVarianceItemSummary,
    InventoryVariancePeriodComparison,
    InventoryVarianceReasonSummary,
)
from app.modules.inventory.domain.repositories.inventory_item_repository import (
    InventoryItemRepository,
)


class ListInventoryVarianceActionSuggestionsQuery:
    """Build business-facing next actions from inventory variance read models."""

    SEVERITY_SCORE = {
        "critical": 100,
        "high": 80,
        "medium": 60,
        "low": 30,
        "info": 10,
    }
    ACTION_TARGETS = {
        "complete_item_cost": ("catalog_ingredients", "Ar potlasa"),
        "period_missing_cost": ("catalog_ingredients", "Hianyzo arak"),
        "period_critical": ("inventory_theoretical_stock", "Keszlet kontroll"),
        "period_worsening": ("inventory_theoretical_stock", "Top elteresek"),
        "period_watch": ("inventory_theoretical_stock", "Trend atnezes"),
        "investigate_high_loss_item": ("inventory_theoretical_stock", "Fogyasi naplo"),
        "review_repeating_loss_item": ("inventory_theoretical_stock", "Fogyasi naplo"),
        "watch_item_variance": ("inventory_theoretical_stock", "Fogyasi naplo"),
        "review_surplus_item": ("procurement_invoices", "Beszerzesek"),
        "review_recipe_variance": ("production_recipes", "Receptek"),
        "review_mapping_variance": ("imports", "Mapping review"),
        "review_missing_purchase_invoice": ("procurement_invoices", "Szamlak"),
        "review_waste_process": ("inventory_theoretical_stock", "Selejt kontroll"),
        "review_breakage_process": ("inventory_theoretical_stock", "Tores kontroll"),
        "review_spoilage_process": ("inventory_theoretical_stock", "Romlas kontroll"),
        "review_theft_suspected": ("inventory_theoretical_stock", "Celzott kontroll"),
    }

    def __init__(self, repository: InventoryItemRepository) -> None:
        self.repository = repository

    def execute(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        days: int = 30,
        limit: int = 8,
    ) -> list[InventoryVarianceActionSuggestion]:
        """Return prioritized controlling actions without mutating state."""

        comparison = self.repository.get_variance_period_comparison(
            business_unit_id=business_unit_id,
            days=days,
        )
        item_summaries = self.repository.list_variance_item_summary(
            business_unit_id=business_unit_id,
            limit=max(limit, 10),
        )
        reason_summaries = self.repository.list_variance_reason_summary(
            business_unit_id=business_unit_id,
            limit=5,
        )

        suggestions = [
            *self._period_suggestions(
                comparison=comparison,
                business_unit_id=business_unit_id,
            ),
            *self._item_suggestions(
                item_summaries=item_summaries,
                business_unit_id=business_unit_id,
            ),
            *self._reason_suggestions(
                reason_summaries=reason_summaries,
                business_unit_id=business_unit_id,
            ),
        ]
        if not suggestions:
            suggestions.append(self._routine_monitoring_suggestion())

        suggestions = self._apply_review_states(
            suggestions=suggestions,
            business_unit_id=business_unit_id,
        )
        return sorted(
            suggestions,
            key=lambda suggestion: (
                suggestion.review_status == "resolved",
                -suggestion.priority_score,
                -(suggestion.estimated_impact_value or Decimal("0")),
                suggestion.title,
            ),
        )[:limit]

    def _apply_review_states(
        self,
        *,
        suggestions: list[InventoryVarianceActionSuggestion],
        business_unit_id: uuid.UUID | None,
    ) -> list[InventoryVarianceActionSuggestion]:
        if business_unit_id is None:
            return suggestions

        review_by_suggestion_id = {
            review.suggestion_id: review
            for review in self.repository.list_variance_action_reviews(
                business_unit_id=business_unit_id,
                suggestion_ids=[suggestion.id for suggestion in suggestions],
            )
        }
        return [
            self._with_review_state(
                suggestion=suggestion,
                review=review_by_suggestion_id.get(suggestion.id),
            )
            for suggestion in suggestions
        ]

    @staticmethod
    def _with_review_state(
        *,
        suggestion: InventoryVarianceActionSuggestion,
        review: InventoryVarianceActionReview | None,
    ) -> InventoryVarianceActionSuggestion:
        if review is None:
            return suggestion
        return InventoryVarianceActionSuggestion(
            id=suggestion.id,
            scope=suggestion.scope,
            action_type=suggestion.action_type,
            severity=suggestion.severity,
            priority_score=suggestion.priority_score,
            title=suggestion.title,
            rationale=suggestion.rationale,
            recommended_action=suggestion.recommended_action,
            inventory_item_id=suggestion.inventory_item_id,
            inventory_item_name=suggestion.inventory_item_name,
            reason_code=suggestion.reason_code,
            estimated_impact_value=suggestion.estimated_impact_value,
            action_target_type=suggestion.action_target_type,
            action_target_label=suggestion.action_target_label,
            action_target_params=suggestion.action_target_params,
            review_status=review.status,
            review_note=review.note,
            reviewed_at=review.resolved_at,
        )

    def _period_suggestions(
        self,
        *,
        comparison: InventoryVariancePeriodComparison,
        business_unit_id: uuid.UUID | None,
    ) -> list[InventoryVarianceActionSuggestion]:
        if comparison.decision_status in {"stable", "improving"}:
            return []

        severity_by_status = {
            "missing_cost": "critical",
            "critical": "critical",
            "worsening": "high",
            "watch": "medium",
        }
        title_by_status = {
            "missing_cost": "Hianyzo beszerzesi arak potlasa",
            "critical": "Magas keszletveszteseg ellenorzese",
            "worsening": "Romlo keszletelteres megallitasa",
            "watch": "Keszletkorrekciok heti atnezese",
        }
        action_by_status = {
            "missing_cost": "Potold a hianyzo beszerzesi arakat, majd futtasd ujra az elteres elemzest.",
            "critical": "Nezd at a top vesztesegu teteleket, az ok kodokat es a fizikai szamolasi naplot.",
            "worsening": "Szurj ra a top vesztesegu tetelekre es az ismert okokra, majd jelolj ki konkret javito lepest.",
            "watch": "Tarts heti kontrollt; ha ugyanaz az ok vagy tetel visszater, emeld javitasi feladatta.",
        }
        status = comparison.decision_status
        severity = severity_by_status.get(status, "medium")
        return [
            self._suggestion(
                id=f"period:{status}",
                scope="period",
                action_type=f"period_{status}",
                severity=severity,
                title=title_by_status.get(status, "Keszletelteres atnezese"),
                rationale=comparison.recommendation,
                recommended_action=action_by_status.get(
                    status,
                    "Nezd at az idoszaki keszletelteresi jelzest.",
                ),
                estimated_impact_value=comparison.current_estimated_shortage_value,
                action_target_params=self._target_params(
                    business_unit_id=business_unit_id,
                ),
            )
        ]

    def _item_suggestions(
        self,
        *,
        item_summaries: list[InventoryVarianceItemSummary],
        business_unit_id: uuid.UUID | None,
    ) -> list[InventoryVarianceActionSuggestion]:
        suggestions: list[InventoryVarianceActionSuggestion] = []
        for item in item_summaries:
            if item.anomaly_status == "normal":
                continue

            if item.anomaly_status == "missing_cost":
                suggestions.append(
                    self._suggestion(
                        id=f"item:{item.inventory_item_id}:missing_cost",
                        scope="item",
                        action_type="complete_item_cost",
                        severity="critical",
                        title=f"{item.name}: beszerzesi ar hianyzik",
                        rationale=(
                            "A tetelnel van veszteseg vagy korrekcio, de nincs "
                            "aktualis beszerzesi ar, ezert a HUF hatas nem megbizhato."
                        ),
                        recommended_action=(
                            "Potold az alapanyag aktualis beszerzesi arat a katalogusban "
                            "vagy a beszerzesi szamla postingbol."
                        ),
                        inventory_item_id=item.inventory_item_id,
                        inventory_item_name=item.name,
                        action_target_params=self._target_params(
                            business_unit_id=business_unit_id,
                            inventory_item_id=item.inventory_item_id,
                            quick_action="complete_item_cost",
                        ),
                    )
                )
                continue

            if item.anomaly_status == "high_loss":
                suggestions.append(
                    self._suggestion(
                        id=f"item:{item.inventory_item_id}:high_loss",
                        scope="item",
                        action_type="investigate_high_loss_item",
                        severity="critical",
                        title=f"{item.name}: magas becsult veszteseg",
                        rationale=(
                            f"{item.shortage_quantity} mennyisegnyi hiany/veszteseg "
                            "jelent meg ezen a keszletelemen."
                        ),
                        recommended_action=(
                            "Ellenorizd a fizikai szamolast, a selejt okokat, a receptet "
                            "es a POS/katalogus mappinget."
                        ),
                        inventory_item_id=item.inventory_item_id,
                        inventory_item_name=item.name,
                        estimated_impact_value=item.estimated_shortage_value,
                        action_target_params=self._target_params(
                            business_unit_id=business_unit_id,
                            inventory_item_id=item.inventory_item_id,
                        ),
                    )
                )
                continue

            if item.anomaly_status == "repeating_loss":
                suggestions.append(
                    self._suggestion(
                        id=f"item:{item.inventory_item_id}:repeating_loss",
                        scope="item",
                        action_type="review_repeating_loss_item",
                        severity="high",
                        title=f"{item.name}: visszatero veszteseg",
                        rationale=(
                            f"{item.movement_count} ok-kodos korrekcio szerepel a tetelen."
                        ),
                        recommended_action=(
                            "Nezd meg, ugyanaz az ok ter vissza-e; ha igen, javits receptet, "
                            "tarolast vagy munkafolyamatot."
                        ),
                        inventory_item_id=item.inventory_item_id,
                        inventory_item_name=item.name,
                        estimated_impact_value=item.estimated_shortage_value,
                        action_target_params=self._target_params(
                            business_unit_id=business_unit_id,
                            inventory_item_id=item.inventory_item_id,
                        ),
                    )
                )
                continue

            if item.anomaly_status == "surplus_review":
                suggestions.append(
                    self._suggestion(
                        id=f"item:{item.inventory_item_id}:surplus_review",
                        scope="item",
                        action_type="review_surplus_item",
                        severity="medium",
                        title=f"{item.name}: tobblet vagy kimaradt fogyas",
                        rationale=(
                            "A tetelnel tobblet korrekcio latszik, ami kimaradt "
                            "beszerzest vagy hianyos fogyasztasi becslest jelezhet."
                        ),
                        recommended_action=(
                            "Ellenorizd, hogy minden beszerzesi szamla postolva van-e, "
                            "illetve a recept/POS fogyas jol csokken-e."
                        ),
                        inventory_item_id=item.inventory_item_id,
                        inventory_item_name=item.name,
                        estimated_impact_value=item.estimated_surplus_value,
                        action_target_params=self._target_params(
                            business_unit_id=business_unit_id,
                            inventory_item_id=item.inventory_item_id,
                        ),
                    )
                )
                continue

            suggestions.append(
                self._suggestion(
                    id=f"item:{item.inventory_item_id}:watch",
                    scope="item",
                    action_type="watch_item_variance",
                    severity="medium",
                    title=f"{item.name}: figyelendo keszletelteres",
                    rationale="A tetelnel hiany vagy veszteseg jelzes jelent meg.",
                    recommended_action=(
                        "Nyisd meg a fogyasi naplot es az ok szerinti bontast, majd "
                        "ellenorizd a kovetkezo fizikai szamolasnal."
                    ),
                    inventory_item_id=item.inventory_item_id,
                    inventory_item_name=item.name,
                    estimated_impact_value=item.estimated_shortage_value,
                    action_target_params=self._target_params(
                        business_unit_id=business_unit_id,
                        inventory_item_id=item.inventory_item_id,
                    ),
                )
            )

        return suggestions

    def _reason_suggestions(
        self,
        *,
        reason_summaries: list[InventoryVarianceReasonSummary],
        business_unit_id: uuid.UUID | None,
    ) -> list[InventoryVarianceActionSuggestion]:
        mapping = {
            "recipe_error": (
                "review_recipe_variance",
                "high",
                "Recept hibak priorizalt atnezese",
                "Recept hiba ok-koddal rogzitett keszletkorrekcio jelent meg.",
                "Nezd at az erintett recepteket, hozamokat es alapanyag mennyisegeket.",
            ),
            "mapping_error": (
                "review_mapping_variance",
                "high",
                "POS/katalogus mapping ellenorzese",
                "Mapping hiba ok-koddal rogzitett keszletkorrekcio jelent meg.",
                "Ellenorizd az aliasokat es a recepthez kotott termekeket.",
            ),
            "missing_purchase_invoice": (
                "review_missing_purchase_invoice",
                "medium",
                "Kimaradt beszerzesek ellenorzese",
                "Kimaradt beszerzes ok-koddal tobblet vagy korrekcio jelent meg.",
                "Nezd at, hogy minden beszerzesi szamla rogzitve es postolva van-e.",
            ),
            "waste": (
                "review_waste_process",
                "medium",
                "Selejt folyamat ellenorzese",
                "Selejt ok-koddal keszletkorrekcio jelent meg.",
                "Nezd at a selejt rogzitest, tarolast es elokeszitesi folyamatot.",
            ),
            "breakage": (
                "review_breakage_process",
                "medium",
                "Tores/kiborulas okok csokkentese",
                "Tores vagy kiborulas ok-koddal korrekcio jelent meg.",
                "Ellenorizd az erintett munkafolyamatot es tarolasi pontokat.",
            ),
            "spoilage": (
                "review_spoilage_process",
                "medium",
                "Romlas okok csokkentese",
                "Romlas ok-koddal keszletkorrekcio jelent meg.",
                "Nezd at a rendelest, tarolast es elokeszitesi mennyisegeket.",
            ),
            "theft_suspected": (
                "review_theft_suspected",
                "critical",
                "Lopasgyanu kontroll",
                "Lopasgyanu ok-koddal keszletkorrekcio jelent meg.",
                "Vegezz celzott fizikai kontrollt es jogosultsagi/folyamat ellenorzest.",
            ),
        }

        suggestions: list[InventoryVarianceActionSuggestion] = []
        for reason in reason_summaries:
            if reason.reason_code not in mapping:
                continue
            action_type, severity, title, rationale, action = mapping[
                reason.reason_code
            ]
            suggestions.append(
                self._suggestion(
                    id=f"reason:{reason.reason_code}",
                    scope="reason",
                    action_type=action_type,
                    severity=severity,
                    title=title,
                    rationale=(
                        f"{rationale} Elofordulasok: {reason.movement_count}, "
                        f"netto keszlethatas: {reason.net_quantity_delta}."
                    ),
                    recommended_action=action,
                    reason_code=reason.reason_code,
                    action_target_params=self._target_params(
                        business_unit_id=business_unit_id,
                        reason_code=reason.reason_code,
                        quick_action=self._reason_quick_action(reason.reason_code),
                        mapping_status=(
                            "pending" if reason.reason_code == "mapping_error" else None
                        ),
                    ),
                )
            )
        return suggestions

    def _routine_monitoring_suggestion(self) -> InventoryVarianceActionSuggestion:
        return self._suggestion(
            id="routine:inventory_variance_monitoring",
            scope="period",
            action_type="routine_monitoring",
            severity="info",
            title="Nincs surgos keszletelteresi akcio",
            rationale="A vizsgalt adatok alapjan nincs kiemelt veszteseg vagy hianyzo ar.",
            recommended_action=(
                "Tartsd meg a heti fizikai szamolasi es elteres-atnezesi ritmust."
            ),
        )

    @staticmethod
    def _reason_quick_action(reason_code: str) -> str | None:
        return {
            "recipe_error": "review_recipe_variance",
            "mapping_error": "review_mapping_variance",
            "missing_purchase_invoice": "review_missing_purchase_invoice",
            "waste": "review_waste_process",
            "breakage": "review_breakage_process",
            "spoilage": "review_spoilage_process",
            "theft_suspected": "review_theft_suspected",
        }.get(reason_code)

    def _suggestion(
        self,
        *,
        id: str,
        scope: str,
        action_type: str,
        severity: str,
        title: str,
        rationale: str,
        recommended_action: str,
        inventory_item_id: uuid.UUID | None = None,
        inventory_item_name: str | None = None,
        reason_code: str | None = None,
        estimated_impact_value: Decimal | None = None,
        action_target_type: str | None = None,
        action_target_label: str | None = None,
        action_target_params: dict[str, str] | None = None,
    ) -> InventoryVarianceActionSuggestion:
        default_target_type, default_target_label = self.ACTION_TARGETS.get(
            action_type,
            (None, None),
        )
        target_type = action_target_type or default_target_type
        target_label = action_target_label or default_target_label
        target_params = dict(action_target_params or {})
        if target_type:
            target_params.setdefault("action_suggestion_id", id)
        return InventoryVarianceActionSuggestion(
            id=id,
            scope=scope,
            action_type=action_type,
            severity=severity,
            priority_score=self.SEVERITY_SCORE[severity],
            title=title,
            rationale=rationale,
            recommended_action=recommended_action,
            inventory_item_id=inventory_item_id,
            inventory_item_name=inventory_item_name,
            reason_code=reason_code,
            estimated_impact_value=estimated_impact_value,
            action_target_type=target_type,
            action_target_label=target_label,
            action_target_params=target_params,
            review_status="open",
            review_note=None,
            reviewed_at=None,
        )

    @staticmethod
    def _target_params(
        *,
        business_unit_id: uuid.UUID | None = None,
        inventory_item_id: uuid.UUID | None = None,
        reason_code: str | None = None,
        mapping_status: str | None = None,
        quick_action: str | None = None,
    ) -> dict[str, str]:
        params: dict[str, str] = {}
        if business_unit_id is not None:
            params["business_unit_id"] = str(business_unit_id)
        if inventory_item_id is not None:
            params["inventory_item_id"] = str(inventory_item_id)
        if reason_code is not None:
            params["reason_code"] = reason_code
        if mapping_status is not None:
            params["mapping_status"] = mapping_status
        if quick_action is not None:
            params["quick_action"] = quick_action
        return params
