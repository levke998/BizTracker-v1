"""POS source product alias ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
    from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
    from app.modules.master_data.infrastructure.orm.business_unit_model import (
        BusinessUnitModel,
    )
    from app.modules.master_data.infrastructure.orm.product_model import ProductModel


class PosProductAliasModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Connects POS-export product identifiers to internal catalog products."""

    __tablename__ = "pos_product_alias"
    __table_args__ = (
        sa.Index("ix_core_pos_product_alias_business_unit_id", "business_unit_id"),
        sa.Index("ix_core_pos_product_alias_product_id", "product_id"),
        sa.Index("ix_core_pos_product_alias_status", "status"),
        sa.Index(
            "ix_core_pos_product_alias_unique_source_key",
            "business_unit_id",
            "source_system",
            "source_product_key",
            unique=True,
        ),
        {"schema": "core"},
    )

    business_unit_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.business_unit.id", ondelete="RESTRICT"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.product.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_system: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    source_product_key: Mapped[str] = mapped_column(sa.String(250), nullable=False)
    source_product_name: Mapped[str] = mapped_column(sa.String(250), nullable=False)
    source_sku: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    source_barcode: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default=sa.text("'auto_created'"),
    )
    mapping_confidence: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default=sa.text("'name_auto'"),
    )
    occurrence_count: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("0"),
    )
    first_seen_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )
    last_import_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("ingest.import_batch.id", ondelete="SET NULL"),
        nullable=True,
    )
    last_import_row_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("ingest.import_row.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )

    business_unit: Mapped["BusinessUnitModel"] = relationship()
    product: Mapped["ProductModel | None"] = relationship()
    last_import_batch: Mapped["ImportBatchModel | None"] = relationship()
    last_import_row: Mapped["ImportRowModel | None"] = relationship()
