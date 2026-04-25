"""Dependency wiring for the demo POS presentation layer."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.demo_pos.application.commands.create_demo_receipt import (
    CreateDemoPosReceiptCommand,
)
from app.modules.demo_pos.application.queries.list_demo_receipts import (
    ListDemoPosReceiptsQuery,
)

DbSession = Annotated[Session, Depends(get_db_session)]


def get_create_demo_pos_receipt_command(
    session: DbSession,
) -> CreateDemoPosReceiptCommand:
    """Wire the demo POS receipt command."""

    return CreateDemoPosReceiptCommand(session)


def get_list_demo_pos_receipts_query(
    session: DbSession,
) -> ListDemoPosReceiptsQuery:
    """Wire the persisted demo POS receipt history query."""

    return ListDemoPosReceiptsQuery(session)
