"""Weather presentation dependency wiring."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.weather.application.commands.backfill_weather import (
    BackfillWeatherCommand,
)
from app.modules.weather.application.commands.backfill_import_batch_weather import (
    BackfillImportBatchWeatherCommand,
)
from app.modules.weather.application.commands.ensure_import_batch_weather_coverage import (
    EnsureImportBatchWeatherCoverageCommand,
)
from app.modules.weather.application.commands.ensure_shared_weather_interval_coverage import (
    EnsureSharedWeatherIntervalCoverageCommand,
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
from app.modules.weather.application.services.weather_provider import (
    OpenMeteoWeatherProvider,
    WeatherProvider,
)
from app.modules.weather.infrastructure.repositories.sqlalchemy_weather_repository import (
    SqlAlchemyWeatherRepository,
)
from app.modules.weather.infrastructure.repositories.sqlalchemy_import_weather_repository import (
    SqlAlchemyImportWeatherRepository,
)

DbSession = Annotated[Session, Depends(get_db_session)]


def get_weather_provider() -> WeatherProvider:
    """Return the active weather provider."""

    return OpenMeteoWeatherProvider()


def get_backfill_weather_command(
    session: DbSession,
    provider: Annotated[WeatherProvider, Depends(get_weather_provider)],
) -> BackfillWeatherCommand:
    """Wire the weather backfill command to its repository and provider."""

    repository = SqlAlchemyWeatherRepository(session)
    return BackfillWeatherCommand(repository=repository, provider=provider)


def get_import_batch_weather_recommendation_query(
    session: DbSession,
) -> GetImportBatchWeatherRecommendationQuery:
    """Wire import-batch weather recommendation."""

    repository = SqlAlchemyImportWeatherRepository(session)
    return GetImportBatchWeatherRecommendationQuery(repository=repository)


def get_backfill_import_batch_weather_command(
    session: DbSession,
    provider: Annotated[WeatherProvider, Depends(get_weather_provider)],
) -> BackfillImportBatchWeatherCommand:
    """Wire import-batch weather backfill."""

    import_weather_repository = SqlAlchemyImportWeatherRepository(session)
    weather_repository = SqlAlchemyWeatherRepository(session)
    recommendation_query = GetImportBatchWeatherRecommendationQuery(
        repository=import_weather_repository
    )
    backfill_command = BackfillWeatherCommand(
        repository=weather_repository,
        provider=provider,
    )
    return BackfillImportBatchWeatherCommand(
        recommendation_query=recommendation_query,
        backfill_command=backfill_command,
    )


def get_ensure_import_batch_weather_coverage_command(
    session: DbSession,
    provider: Annotated[WeatherProvider, Depends(get_weather_provider)],
) -> EnsureImportBatchWeatherCoverageCommand:
    """Wire import-batch weather coverage orchestration."""

    import_weather_repository = SqlAlchemyImportWeatherRepository(session)
    weather_repository = SqlAlchemyWeatherRepository(session)
    recommendation_query = GetImportBatchWeatherRecommendationQuery(
        repository=import_weather_repository
    )
    backfill_weather_command = BackfillWeatherCommand(
        repository=weather_repository,
        provider=provider,
    )
    backfill_import_batch_command = BackfillImportBatchWeatherCommand(
        recommendation_query=recommendation_query,
        backfill_command=backfill_weather_command,
    )
    return EnsureImportBatchWeatherCoverageCommand(
        recommendation_query=recommendation_query,
        backfill_command=backfill_import_batch_command,
    )


def get_sync_shared_weather_command(
    session: DbSession,
    provider: Annotated[WeatherProvider, Depends(get_weather_provider)],
) -> SyncSharedWeatherCommand:
    """Wire shared Szolnok weather sync."""

    weather_repository = SqlAlchemyWeatherRepository(session)
    backfill_command = BackfillWeatherCommand(
        repository=weather_repository,
        provider=provider,
    )
    return SyncSharedWeatherCommand(backfill_command=backfill_command)


def get_sync_shared_weather_forecast_command(
    session: DbSession,
    provider: Annotated[WeatherProvider, Depends(get_weather_provider)],
) -> SyncSharedWeatherForecastCommand:
    """Wire shared Szolnok forecast sync."""

    weather_repository = SqlAlchemyWeatherRepository(session)
    return SyncSharedWeatherForecastCommand(
        repository=weather_repository,
        provider=provider,
    )


def get_ensure_shared_weather_interval_coverage_command(
    session: DbSession,
    provider: Annotated[WeatherProvider, Depends(get_weather_provider)],
) -> EnsureSharedWeatherIntervalCoverageCommand:
    """Wire shared weather interval coverage orchestration."""

    weather_repository = SqlAlchemyWeatherRepository(session)
    backfill_command = BackfillWeatherCommand(
        repository=weather_repository,
        provider=provider,
    )
    return EnsureSharedWeatherIntervalCoverageCommand(
        repository=weather_repository,
        backfill_command=backfill_command,
    )


def get_list_weather_locations_query(session: DbSession) -> ListWeatherLocationsQuery:
    """Wire weather location listing."""

    repository = SqlAlchemyWeatherRepository(session)
    return ListWeatherLocationsQuery(repository=repository)


def get_list_weather_observations_query(session: DbSession) -> ListWeatherObservationsQuery:
    """Wire weather observation listing."""

    repository = SqlAlchemyWeatherRepository(session)
    return ListWeatherObservationsQuery(repository=repository)


def get_list_weather_forecasts_query(session: DbSession) -> ListWeatherForecastsQuery:
    """Wire weather forecast listing."""

    repository = SqlAlchemyWeatherRepository(session)
    return ListWeatherForecastsQuery(repository=repository)
