"""Shared fixtures for backend integration tests."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.main import app
from app.modules.imports.infrastructure.orm.import_batch_model import ImportBatchModel
from app.modules.imports.infrastructure.orm.import_file_model import ImportFileModel
from app.modules.imports.infrastructure.orm.import_row_error_model import (
    ImportRowErrorModel,
)
from app.modules.imports.infrastructure.orm.import_row_model import ImportRowModel
from app.modules.master_data.infrastructure.orm.business_unit_model import (
    BusinessUnitModel,
)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Yield a FastAPI test client against the real app wiring."""

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Yield a direct SQLAlchemy session for verification and cleanup."""

    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def imports_fixtures_dir() -> Path:
    """Return the directory that stores CSV fixtures for import tests."""

    return Path(__file__).resolve().parent / "fixtures" / "imports"


@pytest.fixture
def test_business_unit(db_session: Session) -> Generator[BusinessUnitModel, None, None]:
    """Create a dedicated business unit and clean all related import data after use."""

    business_unit = BusinessUnitModel(
        code=f"test-{uuid4().hex[:8]}",
        name="Integration Test Unit",
        type="test",
        is_active=True,
    )
    db_session.add(business_unit)
    db_session.commit()
    db_session.refresh(business_unit)

    yield business_unit

    db_session.rollback()
    db_session.expire_all()

    file_paths = [
        Path(stored_path)
        for stored_path, in db_session.execute(
            select(ImportFileModel.stored_path)
            .join(ImportBatchModel, ImportFileModel.batch_id == ImportBatchModel.id)
            .where(ImportBatchModel.business_unit_id == business_unit.id)
        ).all()
    ]
    batch_ids = [
        batch_id
        for batch_id, in db_session.execute(
            select(ImportBatchModel.id).where(
                ImportBatchModel.business_unit_id == business_unit.id
            )
        ).all()
    ]

    if batch_ids:
        db_session.execute(
            delete(ImportRowErrorModel).where(ImportRowErrorModel.batch_id.in_(batch_ids))
        )
        db_session.execute(
            delete(ImportRowModel).where(ImportRowModel.batch_id.in_(batch_ids))
        )
        db_session.execute(
            delete(ImportFileModel).where(ImportFileModel.batch_id.in_(batch_ids))
        )
        db_session.execute(delete(ImportBatchModel).where(ImportBatchModel.id.in_(batch_ids)))

    db_session.execute(
        delete(BusinessUnitModel).where(BusinessUnitModel.id == business_unit.id)
    )
    db_session.commit()

    for file_path in file_paths:
        if file_path.exists():
            file_path.unlink()
