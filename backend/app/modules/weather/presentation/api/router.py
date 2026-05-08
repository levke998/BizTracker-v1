"""Weather API router."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.modules.weather.application.commands.backfill_weather import (
    BackfillWeatherCommand,
    WeatherBusinessUnitNotFoundError,
    WeatherLocationMismatchError,
    WeatherValidationError,
)
from app.modules.weather.application.commands.backfill_import_batch_weather import (
    BackfillImportBatchWeatherCommand,
    ImportBatchWeatherNotFoundError,
)
from app.modules.weather.application.commands.ensure_import_batch_weather_coverage import (
    EnsureImportBatchWeatherCoverageCommand,
)
from app.modules.weather.application.commands.sync_shared_weather import (
    SyncSharedWeatherCommand,
)
from app.modules.weather.application.commands.sync_shared_weather_forecast import (
    SyncSharedWeatherForecastCommand,
)
from app.modules.weather.application.queries.list_weather import (
    ListWeatherForecastsQuery,
    ListWeatherLocationsQuery,
    ListWeatherObservationsQuery,
)
from app.modules.weather.application.queries.import_batch_weather import (
    GetImportBatchWeatherRecommendationQuery,
)
from app.modules.weather.presentation.dependencies import (
    get_backfill_import_batch_weather_command,
    get_backfill_weather_command,
    get_ensure_import_batch_weather_coverage_command,
    get_import_batch_weather_recommendation_query,
    get_list_weather_forecasts_query,
    get_list_weather_locations_query,
    get_list_weather_observations_query,
    get_sync_shared_weather_command,
    get_sync_shared_weather_forecast_command,
)
from app.modules.weather.presentation.schemas.weather import (
    ImportBatchWeatherCoverageResponse,
    ImportBatchWeatherRecommendationResponse,
    WeatherBackfillRequest,
    WeatherBackfillResponse,
    WeatherForecastResponse,
    WeatherForecastSyncResponse,
    WeatherLocationResponse,
    WeatherObservationResponse,
)

router = APIRouter(prefix="/weather", tags=["weather"])


@router.post(
    "/sync/szolnok",
    response_model=WeatherBackfillResponse,
    status_code=status.HTTP_201_CREATED,
)
def sync_shared_szolnok_weather(
    command: Annotated[SyncSharedWeatherCommand, Depends(get_sync_shared_weather_command)],
    days_back: int = Query(default=2, ge=0, le=30),
) -> WeatherBackfillResponse:
    """Sync the shared hourly Szolnok weather cache used by all local businesses."""

    try:
        summary = command.execute(days_back=days_back)
    except WeatherValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    return WeatherBackfillResponse.model_validate(summary)


@router.post(
    "/forecast/szolnok/sync",
    response_model=WeatherForecastSyncResponse,
    status_code=status.HTTP_201_CREATED,
)
def sync_shared_szolnok_weather_forecast(
    command: Annotated[
        SyncSharedWeatherForecastCommand,
        Depends(get_sync_shared_weather_forecast_command),
    ],
    forecast_days: int = Query(default=7, ge=1, le=16),
) -> WeatherForecastSyncResponse:
    """Sync the shared hourly Szolnok forecast cache used by planning features."""

    try:
        summary = command.execute(forecast_days=forecast_days)
    except WeatherValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    return WeatherForecastSyncResponse.model_validate(summary)


@router.get(
    "/import-batches/{batch_id}/recommendation",
    response_model=ImportBatchWeatherRecommendationResponse,
)
def get_import_batch_weather_recommendation(
    batch_id: uuid.UUID,
    query: Annotated[
        GetImportBatchWeatherRecommendationQuery,
        Depends(get_import_batch_weather_recommendation_query),
    ],
) -> ImportBatchWeatherRecommendationResponse:
    """Return weather backfill recommendation for one parsed POS import batch."""

    try:
        recommendation = query.execute(batch_id=batch_id)
    except ImportBatchWeatherNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ImportBatchWeatherRecommendationResponse.model_validate(recommendation)


@router.post(
    "/import-batches/{batch_id}/ensure-coverage",
    response_model=ImportBatchWeatherCoverageResponse,
    status_code=status.HTTP_201_CREATED,
)
def ensure_import_batch_weather_coverage(
    batch_id: uuid.UUID,
    command: Annotated[
        EnsureImportBatchWeatherCoverageCommand,
        Depends(get_ensure_import_batch_weather_coverage_command),
    ],
) -> ImportBatchWeatherCoverageResponse:
    """Ensure shared Szolnok weather cache coverage for one parsed POS import batch."""

    try:
        result = command.execute(batch_id=batch_id)
    except ImportBatchWeatherNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (WeatherBusinessUnitNotFoundError, WeatherLocationMismatchError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except WeatherValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return ImportBatchWeatherCoverageResponse.model_validate(result)


@router.post(
    "/import-batches/{batch_id}/backfill",
    response_model=WeatherBackfillResponse,
    status_code=status.HTTP_201_CREATED,
)
def backfill_import_batch_weather(
    batch_id: uuid.UUID,
    command: Annotated[
        BackfillImportBatchWeatherCommand,
        Depends(get_backfill_import_batch_weather_command),
    ],
) -> WeatherBackfillResponse:
    """Cache weather observations for the date range covered by one import batch."""

    try:
        summary = command.execute(batch_id=batch_id)
    except ImportBatchWeatherNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (WeatherBusinessUnitNotFoundError, WeatherLocationMismatchError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except WeatherValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return WeatherBackfillResponse.model_validate(summary)


@router.get("/locations", response_model=list[WeatherLocationResponse])
def list_weather_locations(
    query: Annotated[
        ListWeatherLocationsQuery,
        Depends(get_list_weather_locations_query),
    ],
    business_unit_id: uuid.UUID | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[WeatherLocationResponse]:
    """Return cached weather lookup locations."""

    locations = query.execute(
        business_unit_id=business_unit_id,
        is_active=is_active,
        limit=limit,
    )
    return [WeatherLocationResponse.model_validate(location) for location in locations]


@router.get("/observations", response_model=list[WeatherObservationResponse])
def list_weather_observations(
    query: Annotated[
        ListWeatherObservationsQuery,
        Depends(get_list_weather_observations_query),
    ],
    business_unit_id: uuid.UUID | None = Query(default=None),
    weather_location_id: uuid.UUID | None = Query(default=None),
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=5000),
) -> list[WeatherObservationResponse]:
    """Return cached hourly weather observations."""

    observations = query.execute(
        business_unit_id=business_unit_id,
        weather_location_id=weather_location_id,
        start_at=start_at,
        end_at=end_at,
        limit=limit,
    )
    return [
        WeatherObservationResponse.model_validate(observation)
        for observation in observations
    ]


@router.get("/forecasts", response_model=list[WeatherForecastResponse])
def list_weather_forecasts(
    query: Annotated[
        ListWeatherForecastsQuery,
        Depends(get_list_weather_forecasts_query),
    ],
    weather_location_id: uuid.UUID | None = Query(default=None),
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=5000),
) -> list[WeatherForecastResponse]:
    """Return cached hourly forecast rows."""

    forecasts = query.execute(
        weather_location_id=weather_location_id,
        start_at=start_at,
        end_at=end_at,
        limit=limit,
    )
    return [WeatherForecastResponse.model_validate(forecast) for forecast in forecasts]


@router.post(
    "/backfill",
    response_model=WeatherBackfillResponse,
    status_code=status.HTTP_201_CREATED,
)
def backfill_weather(
    payload: WeatherBackfillRequest,
    command: Annotated[BackfillWeatherCommand, Depends(get_backfill_weather_command)],
) -> WeatherBackfillResponse:
    """Cache hourly weather observations for a business unit and date range."""

    try:
        summary = command.execute(**payload.model_dump())
    except WeatherBusinessUnitNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (WeatherLocationMismatchError, WeatherValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return WeatherBackfillResponse.model_validate(summary)
