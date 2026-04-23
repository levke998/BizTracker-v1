"""Read-only master data API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

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
from app.modules.master_data.presentation.dependencies import (
    get_business_unit_query,
    get_category_query,
    get_location_query,
    get_product_query,
    get_unit_of_measure_query,
)
from app.modules.master_data.presentation.schemas.business_unit import (
    BusinessUnitResponse,
)
from app.modules.master_data.presentation.schemas.category import CategoryResponse
from app.modules.master_data.presentation.schemas.location import LocationResponse
from app.modules.master_data.presentation.schemas.product import ProductResponse
from app.modules.master_data.presentation.schemas.unit_of_measure import (
    UnitOfMeasureResponse,
)

router = APIRouter(prefix="/master-data", tags=["master-data"])


@router.get("/business-units", response_model=list[BusinessUnitResponse])
def list_business_units(
    query: Annotated[ListBusinessUnitsQuery, Depends(get_business_unit_query)],
    active_only: bool = Query(default=True),
) -> list[BusinessUnitResponse]:
    """Return read-only business units."""

    items = query.execute(active_only=active_only)
    return [BusinessUnitResponse.model_validate(item) for item in items]


@router.get("/locations", response_model=list[LocationResponse])
def list_locations(
    business_unit_id: uuid.UUID,
    query: Annotated[ListLocationsQuery, Depends(get_location_query)],
    active_only: bool = Query(default=True),
) -> list[LocationResponse]:
    """Return read-only locations for a business unit."""

    items = query.execute(business_unit_id=business_unit_id, active_only=active_only)
    return [LocationResponse.model_validate(item) for item in items]


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(
    business_unit_id: uuid.UUID,
    query: Annotated[ListCategoriesQuery, Depends(get_category_query)],
    active_only: bool = Query(default=True),
) -> list[CategoryResponse]:
    """Return read-only categories for a business unit."""

    items = query.execute(business_unit_id=business_unit_id, active_only=active_only)
    return [CategoryResponse.model_validate(item) for item in items]


@router.get("/products", response_model=list[ProductResponse])
def list_products(
    business_unit_id: uuid.UUID,
    query: Annotated[ListProductsQuery, Depends(get_product_query)],
    active_only: bool = Query(default=True),
) -> list[ProductResponse]:
    """Return read-only products for a business unit."""

    items = query.execute(business_unit_id=business_unit_id, active_only=active_only)
    return [ProductResponse.model_validate(item) for item in items]


@router.get("/units-of-measure", response_model=list[UnitOfMeasureResponse])
def list_units_of_measure(
    query: Annotated[ListUnitsOfMeasureQuery, Depends(get_unit_of_measure_query)],
) -> list[UnitOfMeasureResponse]:
    """Return read-only units of measure."""

    items = query.execute()
    return [UnitOfMeasureResponse.model_validate(item) for item in items]
