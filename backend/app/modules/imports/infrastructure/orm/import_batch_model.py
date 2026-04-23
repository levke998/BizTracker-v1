"""Import batch ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.imports.infrastructure.orm.import_file_model import ImportFileModel
    from app.modules.imports.infrastructure.orm.import_row_error_model import (
        ImportRowErrorModel,
    )
    from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel


class ImportBatchModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stores metadata for a logical import batch."""

    __tablename__ = "import_batch"
    __table_args__ = (
        sa.Index("ix_ingest_import_batch_business_unit_id", "business_unit_id"),
        sa.Index("ix_ingest_import_batch_status", "status"),
        sa.Index("ix_ingest_import_batch_created_at", "created_at"),
        {"schema": "ingest"},
    )

    business_unit_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.business_unit.id", ondelete="RESTRICT"),
        nullable=False,
    )
    import_type: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default=sa.text("'uploaded'"),
    )
    started_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )
    total_rows: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("0"),
    )
    parsed_rows: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("0"),
    )
    error_rows: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("0"),
    )

    files: Mapped[list["ImportFileModel"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
        order_by="ImportFileModel.uploaded_at.desc()",
    )
    rows: Mapped[list["ImportRowModel"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
        order_by="ImportRowModel.row_number.asc()",
    )
    errors: Mapped[list["ImportRowErrorModel"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
        order_by="ImportRowErrorModel.created_at.asc()",
    )
