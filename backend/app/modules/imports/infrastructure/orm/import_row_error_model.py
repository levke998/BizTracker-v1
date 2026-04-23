"""Import row error ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
    from app.modules.imports.infrastructure.orm.import_file_model import ImportFileModel


class ImportRowErrorModel(UUIDPrimaryKeyMixin, Base):
    """Stores parse errors captured during staging import."""

    __tablename__ = "import_row_error"
    __table_args__ = (
        sa.Index("ix_ingest_import_row_error_batch_id", "batch_id"),
        sa.Index("ix_ingest_import_row_error_file_id", "file_id"),
        {"schema": "ingest"},
    )

    batch_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("ingest.import_batch.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("ingest.import_file.id", ondelete="CASCADE"),
        nullable=False,
    )
    row_number: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    field_name: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    error_code: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    message: Mapped[str] = mapped_column(sa.Text, nullable=False)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    batch: Mapped["ImportBatchModel"] = relationship(back_populates="errors")
    file: Mapped["ImportFileModel"] = relationship(back_populates="errors")
