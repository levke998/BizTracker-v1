"""Dependency wiring for the master data presentation layer."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.master_data.application.queries.list_business_units import (
    ListBusinessUnitsQuery,
)
from app.modules.master_data.application.queries.list_categories import (
    ListCategoriesQuery,
)
from app.modules.master_data.application.queries.list_locations import (
    ListLocationsQuery,
)
from app.modules.master_data.application.queries.list_products import (
    ListProductsQuery,
)
from app.modules.master_data.application.queries.list_units_of_measure import (
    ListUnitsOfMeasureQuery,
)
from app.modules.master_data.application.queries.list_vat_rates import ListVatRatesQuery
from app.modules.master_data.infrastructure.repositories.sqlalchemy_business_unit_repository import (
    SqlAlchemyBusinessUnitRepository,
)
from app.modules.master_data.infrastructure.repositories.sqlalchemy_category_repository import (
    SqlAlchemyCategoryRepository,
)
from app.modules.master_data.infrastructure.repositories.sqlalchemy_location_repository import (
    SqlAlchemyLocationRepository,
)
from app.modules.master_data.infrastructure.repositories.sqlalchemy_product_repository import (
    SqlAlchemyProductRepository,
)
from app.modules.master_data.infrastructure.repositories.sqlalchemy_unit_of_measure_repository import (
    SqlAlchemyUnitOfMeasureRepository,
)
from app.modules.master_data.infrastructure.repositories.sqlalchemy_vat_rate_repository import (
    SqlAlchemyVatRateRepository,
)

DbSession = Annotated[Session, Depends(get_db_session)]


def get_business_unit_query(session: DbSession) -> ListBusinessUnitsQuery:
    """Wire the business unit list query to its repository."""

    repository = SqlAlchemyBusinessUnitRepository(session)
    return ListBusinessUnitsQuery(repository)


def get_location_query(session: DbSession) -> ListLocationsQuery:
    """Wire the location list query to its repository."""

    repository = SqlAlchemyLocationRepository(session)
    return ListLocationsQuery(repository)


def get_category_query(session: DbSession) -> ListCategoriesQuery:
    """Wire the category list query to its repository."""

    repository = SqlAlchemyCategoryRepository(session)
    return ListCategoriesQuery(repository)


def get_product_query(session: DbSession) -> ListProductsQuery:
    """Wire the product list query to its repository."""

    repository = SqlAlchemyProductRepository(session)
    return ListProductsQuery(repository)


def get_unit_of_measure_query(session: DbSession) -> ListUnitsOfMeasureQuery:
    """Wire the unit-of-measure list query to its repository."""

    repository = SqlAlchemyUnitOfMeasureRepository(session)
    return ListUnitsOfMeasureQuery(repository)


def get_vat_rate_query(session: DbSession) -> ListVatRatesQuery:
    """Wire the VAT rate list query to its repository."""

    repository = SqlAlchemyVatRateRepository(session)
    return ListVatRatesQuery(repository)
