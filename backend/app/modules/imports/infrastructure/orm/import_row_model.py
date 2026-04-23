"""Import row staging ORM model."""

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


class ImportRowModel(UUIDPrimaryKeyMixin, Base):
    """Stores one parsed CSV row at staging/meta level."""

    __tablename__ = "import_row"
    __table_args__ = (
        sa.Index("ix_ingest_import_row_batch_id", "batch_id"),
        sa.Index("ix_ingest_import_row_file_id", "file_id"),
        sa.Index("ix_ingest_import_row_parse_status", "parse_status"),
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
    row_number: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    normalized_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    parse_status: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    batch: Mapped["ImportBatchModel"] = relationship(back_populates="rows")
    file: Mapped["ImportFileModel"] = relationship(back_populates="rows")
