"""Import file ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
    from app.modules.imports.infrastructure.orm.import_row_error_model import (
        ImportRowErrorModel,
    )
    from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel


class ImportFileModel(UUIDPrimaryKeyMixin, Base):
    """Stores metadata for one uploaded import file."""

    __tablename__ = "import_file"
    __table_args__ = (
        sa.Index("ix_ingest_import_file_batch_id", "batch_id"),
        {"schema": "ingest"},
    )

    batch_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("ingest.import_batch.id", ondelete="CASCADE"),
        nullable=False,
    )
    original_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    size_bytes: Mapped[int] = mapped_column(sa.BigInteger, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    batch: Mapped["ImportBatchModel"] = relationship(back_populates="files")
    rows: Mapped[list["ImportRowModel"]] = relationship(
        back_populates="file",
        cascade="all, delete-orphan",
        order_by="ImportRowModel.row_number.asc()",
    )
    errors: Mapped[list["ImportRowErrorModel"]] = relationship(
        back_populates="file",
        cascade="all, delete-orphan",
        order_by="ImportRowErrorModel.created_at.asc()",
    )
