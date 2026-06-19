"""Application service for POS product alias review and approval."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import uuid

from app.modules.pos_ingestion.domain.entities.product_alias import (
    PosMappingReadiness,
    PosProductAlias,
)
from app.modules.pos_ingestion.domain.repositories.product_alias_repository import (
    PosProductAliasRepository,
)


class PosProductAliasNotFoundError(Exception):
    """Raised when one or more requested POS product aliases do not exist."""


class PosProductAliasProductMismatchError(Exception):
    """Raised when a selected product cannot be used for an alias."""


class PosProductAliasBulkValidationError(Exception):
    """Raised when a bulk review request is structurally invalid."""


@dataclass(frozen=True, slots=True)
class PosProductAliasMapping:
    """One requested alias-to-product approval."""

    alias_id: uuid.UUID
    product_id: uuid.UUID
    notes: str | None = None


class PosProductAliasMappingService:
    """Coordinate transactional POS alias review operations."""

    def __init__(self, repository: PosProductAliasRepository) -> None:
        self._repository = repository

    def list_aliases(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[PosProductAlias]:
        return self._repository.list_aliases(
            business_unit_id=business_unit_id,
            status=status,
        )

    def approve_mapping(
        self,
        *,
        alias_id: uuid.UUID,
        product_id: uuid.UUID,
        notes: str | None = None,
    ) -> PosProductAlias:
        """Approve one alias through the same transactional bulk use case."""

        return self.approve_mappings(
            mappings=(
                PosProductAliasMapping(
                    alias_id=alias_id,
                    product_id=product_id,
                    notes=notes,
                ),
            )
        )[0]

    def approve_mappings(
        self,
        *,
        mappings: tuple[PosProductAliasMapping, ...],
    ) -> list[PosProductAlias]:
        """Validate and approve multiple aliases atomically."""

        if not mappings:
            raise PosProductAliasBulkValidationError(
                "At least one POS product alias mapping is required."
            )

        alias_ids = tuple(mapping.alias_id for mapping in mappings)
        if len(set(alias_ids)) != len(alias_ids):
            raise PosProductAliasBulkValidationError(
                "Each POS product alias can appear only once in a bulk request."
            )

        aliases_by_id = {
            alias.id: alias
            for alias in self._repository.get_aliases(alias_ids)
        }
        missing_alias_ids = [
            alias_id for alias_id in alias_ids if alias_id not in aliases_by_id
        ]
        if missing_alias_ids:
            missing_values = ", ".join(str(alias_id) for alias_id in missing_alias_ids)
            raise PosProductAliasNotFoundError(
                f"POS product aliases were not found: {missing_values}."
            )

        reviewed_aliases: list[PosProductAlias] = []
        for mapping in mappings:
            alias = aliases_by_id[mapping.alias_id]
            if not self._repository.product_belongs_to_business_unit(
                product_id=mapping.product_id,
                business_unit_id=alias.business_unit_id,
            ):
                raise PosProductAliasProductMismatchError(
                    "The selected product does not belong to the alias business unit "
                    f"(alias_id={alias.id})."
                )
            alias.approve(product_id=mapping.product_id, notes=mapping.notes)
            reviewed_aliases.append(alias)

        return self._repository.save_aliases(tuple(reviewed_aliases))

    def get_mapping_readiness(
        self,
        *,
        business_unit_id: uuid.UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> PosMappingReadiness:
        """Return alias, row and gross-revenue mapping coverage."""

        if start_date is not None and end_date is not None and start_date > end_date:
            raise PosProductAliasBulkValidationError(
                "Mapping readiness start_date must be before end_date."
            )
        return self._repository.get_mapping_readiness(
            business_unit_id=business_unit_id,
            start_date=start_date,
            end_date=end_date,
        )
