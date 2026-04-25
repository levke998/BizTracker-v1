"""Production recipe ORM models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.inventory.infrastructure.orm.inventory_item_model import (
        InventoryItemModel,
    )
    from app.modules.master_data.infrastructure.orm.product_model import ProductModel
    from app.modules.master_data.infrastructure.orm.unit_of_measure_model import (
        UnitOfMeasureModel,
    )


class RecipeModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A recipe attached to one sellable product."""

    __tablename__ = "recipe"
    __table_args__ = (
        sa.UniqueConstraint("product_id", "name", name="uq_core_recipe_product_name"),
        sa.Index("ix_core_recipe_product_id", "product_id"),
        {"schema": "core"},
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.product.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )

    product: Mapped["ProductModel"] = relationship()
    versions: Mapped[list["RecipeVersionModel"]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="RecipeVersionModel.version_no.desc()",
    )


class RecipeVersionModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Versioned recipe quantities and yield."""

    __tablename__ = "recipe_version"
    __table_args__ = (
        sa.UniqueConstraint(
            "recipe_id",
            "version_no",
            name="uq_core_recipe_version_recipe_version_no",
        ),
        sa.Index("ix_core_recipe_version_recipe_id", "recipe_id"),
        {"schema": "core"},
    )

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.recipe.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_no: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )
    valid_from: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
    yield_quantity: Mapped[Decimal] = mapped_column(sa.Numeric(12, 3), nullable=False)
    yield_uom_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.unit_of_measure.id", ondelete="RESTRICT"),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)

    recipe: Mapped["RecipeModel"] = relationship(back_populates="versions")
    yield_uom: Mapped["UnitOfMeasureModel"] = relationship()
    ingredients: Mapped[list["RecipeIngredientModel"]] = relationship(
        back_populates="recipe_version",
        cascade="all, delete-orphan",
        order_by="RecipeIngredientModel.created_at.asc()",
    )


class RecipeIngredientModel(UUIDPrimaryKeyMixin, Base):
    """One ingredient quantity inside a recipe version."""

    __tablename__ = "recipe_ingredient"
    __table_args__ = (
        sa.UniqueConstraint(
            "recipe_version_id",
            "inventory_item_id",
            name="uq_core_recipe_ingredient_version_item",
        ),
        sa.Index("ix_core_recipe_ingredient_recipe_version_id", "recipe_version_id"),
        sa.Index("ix_core_recipe_ingredient_inventory_item_id", "inventory_item_id"),
        {"schema": "core"},
    )

    recipe_version_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.recipe_version.id", ondelete="CASCADE"),
        nullable=False,
    )
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.inventory_item.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(sa.Numeric(12, 3), nullable=False)
    uom_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("core.unit_of_measure.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    recipe_version: Mapped["RecipeVersionModel"] = relationship(
        back_populates="ingredients"
    )
    inventory_item: Mapped["InventoryItemModel"] = relationship()
    uom: Mapped["UnitOfMeasureModel"] = relationship()
