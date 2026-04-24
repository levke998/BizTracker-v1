"""Procurement presentation dependency wiring."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.procurement.application.commands.create_purchase_invoice import (
    CreatePurchaseInvoiceCommand,
)
from app.modules.procurement.application.commands.post_purchase_invoice import (
    PostPurchaseInvoiceCommand,
)
from app.modules.procurement.application.commands.create_supplier import (
    CreateSupplierCommand,
)
from app.modules.procurement.application.queries.list_purchase_invoices import (
    ListPurchaseInvoicesQuery,
)
from app.modules.procurement.application.queries.list_suppliers import ListSuppliersQuery
from app.modules.procurement.infrastructure.repositories.sqlalchemy_purchase_invoice_repository import (
    SqlAlchemyPurchaseInvoiceRepository,
)
from app.modules.procurement.infrastructure.repositories.sqlalchemy_supplier_repository import (
    SqlAlchemySupplierRepository,
)

DbSession = Annotated[Session, Depends(get_db_session)]


def get_list_suppliers_query(session: DbSession) -> ListSuppliersQuery:
    """Wire the supplier list query to its repository."""

    repository = SqlAlchemySupplierRepository(session)
    return ListSuppliersQuery(repository=repository)


def get_create_supplier_command(session: DbSession) -> CreateSupplierCommand:
    """Wire the supplier create command to its repository."""

    repository = SqlAlchemySupplierRepository(session)
    return CreateSupplierCommand(repository=repository)


def get_list_purchase_invoices_query(session: DbSession) -> ListPurchaseInvoicesQuery:
    """Wire the purchase invoice list query to its repository."""

    repository = SqlAlchemyPurchaseInvoiceRepository(session)
    return ListPurchaseInvoicesQuery(repository=repository)


def get_create_purchase_invoice_command(session: DbSession) -> CreatePurchaseInvoiceCommand:
    """Wire the purchase invoice create command to its repository."""

    repository = SqlAlchemyPurchaseInvoiceRepository(session)
    return CreatePurchaseInvoiceCommand(repository=repository)


def get_post_purchase_invoice_command(session: DbSession) -> PostPurchaseInvoiceCommand:
    """Wire the purchase invoice posting command to its repository."""

    repository = SqlAlchemyPurchaseInvoiceRepository(session)
    return PostPurchaseInvoiceCommand(repository=repository)
