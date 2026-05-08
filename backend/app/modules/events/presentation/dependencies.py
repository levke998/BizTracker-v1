"""Events presentation dependency wiring."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.events.application.commands.create_event import (
    ArchiveEventCommand,
    CreateEventCommand,
    UpdateEventCommand,
)
from app.modules.events.application.commands.ensure_event_weather_coverage import (
    EnsureEventWeatherCoverageCommand,
)
from app.modules.events.application.commands.upsert_event_ticket_actual import (
    UpsertEventTicketActualCommand,
)
from app.modules.events.application.queries.get_event_ticket_actual import (
    GetEventTicketActualQuery,
)
from app.modules.events.application.queries.list_events import ListEventsQuery
from app.modules.events.application.queries.get_event_performance import (
    GetEventPerformanceQuery,
    ListEventPerformancesQuery,
)
from app.modules.events.infrastructure.repositories.sqlalchemy_event_performance_repository import (
    SqlAlchemyEventPerformanceRepository,
)
from app.modules.events.infrastructure.repositories.sqlalchemy_event_repository import (
    SqlAlchemyEventRepository,
)
from app.modules.events.infrastructure.repositories.sqlalchemy_event_ticket_actual_repository import (
    SqlAlchemyEventTicketActualRepository,
)
from app.modules.weather.application.commands.backfill_weather import BackfillWeatherCommand
from app.modules.weather.application.commands.ensure_shared_weather_interval_coverage import (
    EnsureSharedWeatherIntervalCoverageCommand,
)
from app.modules.weather.infrastructure.repositories.sqlalchemy_weather_repository import (
    SqlAlchemyWeatherRepository,
)
from app.modules.weather.presentation.dependencies import get_weather_provider
from app.modules.weather.application.services.weather_provider import WeatherProvider

DbSession = Annotated[Session, Depends(get_db_session)]


def get_list_events_query(session: DbSession) -> ListEventsQuery:
    """Wire the event list query to its repository."""

    repository = SqlAlchemyEventRepository(session)
    return ListEventsQuery(repository=repository)


def get_event_performance_query(session: DbSession) -> GetEventPerformanceQuery:
    """Wire the event performance query to its read-model repository."""

    repository = SqlAlchemyEventPerformanceRepository(session)
    return GetEventPerformanceQuery(repository=repository)


def get_list_event_performances_query(session: DbSession) -> ListEventPerformancesQuery:
    """Wire the event performance list query to its read-model repository."""

    repository = SqlAlchemyEventPerformanceRepository(session)
    return ListEventPerformancesQuery(repository=repository)


def get_event_ticket_actual_query(session: DbSession) -> GetEventTicketActualQuery:
    """Wire the event ticket actual query."""

    repository = SqlAlchemyEventTicketActualRepository(session)
    return GetEventTicketActualQuery(repository=repository)


def get_create_event_command(session: DbSession) -> CreateEventCommand:
    """Wire the event create command to its repository."""

    repository = SqlAlchemyEventRepository(session)
    return CreateEventCommand(repository=repository)


def get_update_event_command(session: DbSession) -> UpdateEventCommand:
    """Wire the event update command to its repository."""

    repository = SqlAlchemyEventRepository(session)
    return UpdateEventCommand(repository=repository)


def get_upsert_event_ticket_actual_command(
    session: DbSession,
) -> UpsertEventTicketActualCommand:
    """Wire the event ticket actual upsert command."""

    repository = SqlAlchemyEventTicketActualRepository(session)
    return UpsertEventTicketActualCommand(repository=repository)


def get_ensure_event_weather_coverage_command(
    session: DbSession,
    provider: Annotated[WeatherProvider, Depends(get_weather_provider)],
) -> EnsureEventWeatherCoverageCommand:
    """Wire event weather coverage orchestration."""

    event_repository = SqlAlchemyEventRepository(session)
    weather_repository = SqlAlchemyWeatherRepository(session)
    backfill_command = BackfillWeatherCommand(
        repository=weather_repository,
        provider=provider,
    )
    interval_coverage_command = EnsureSharedWeatherIntervalCoverageCommand(
        repository=weather_repository,
        backfill_command=backfill_command,
    )
    return EnsureEventWeatherCoverageCommand(
        repository=event_repository,
        weather_coverage_command=interval_coverage_command,
    )


def get_archive_event_command(session: DbSession) -> ArchiveEventCommand:
    """Wire the event archive command to its repository."""

    repository = SqlAlchemyEventRepository(session)
    return ArchiveEventCommand(repository=repository)
