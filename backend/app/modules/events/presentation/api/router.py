"""Events API router."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.modules.events.application.commands.create_event import (
    ArchiveEventCommand,
    CreateEventCommand,
    EventBusinessUnitNotFoundError,
    EventLocationMismatchError,
    EventNotFoundError,
    EventValidationError,
    UpdateEventCommand,
)
from app.modules.events.application.commands.ensure_event_weather_coverage import (
    EnsureEventWeatherCoverageCommand,
)
from app.modules.events.application.commands.upsert_event_ticket_actual import (
    EventTicketActualValidationError,
    UpsertEventTicketActualCommand,
)
from app.modules.events.application.queries.get_event_ticket_actual import (
    GetEventTicketActualQuery,
)
from app.modules.events.application.queries.list_events import ListEventsQuery
from app.modules.events.application.queries.get_event_performance import (
    EventPerformanceNotFoundError,
    GetEventPerformanceQuery,
    ListEventPerformancesQuery,
)
from app.modules.events.presentation.dependencies import (
    get_archive_event_command,
    get_create_event_command,
    get_ensure_event_weather_coverage_command,
    get_event_performance_query,
    get_list_event_performances_query,
    get_list_events_query,
    get_event_ticket_actual_query,
    get_update_event_command,
    get_upsert_event_ticket_actual_command,
)
from app.modules.events.presentation.schemas.event import (
    EventCreateRequest,
    EventPerformanceResponse,
    EventResponse,
    EventTicketActualRequest,
    EventTicketActualResponse,
    EventWeatherCoverageResponse,
)
from app.modules.weather.application.commands.backfill_weather import WeatherValidationError

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventResponse])
def list_events(
    query: Annotated[ListEventsQuery, Depends(get_list_events_query)],
    business_unit_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    starts_from: datetime | None = Query(default=None),
    starts_to: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[EventResponse]:
    """Return event planning records."""

    events = query.execute(
        business_unit_id=business_unit_id,
        status=status,
        is_active=is_active,
        starts_from=starts_from,
        starts_to=starts_to,
        limit=limit,
    )
    return [EventResponse.model_validate(event) for event in events]


@router.get("/performance", response_model=list[EventPerformanceResponse])
def list_event_performances(
    query: Annotated[
        ListEventPerformancesQuery,
        Depends(get_list_event_performances_query),
    ],
    business_unit_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    starts_from: datetime | None = Query(default=None),
    starts_to: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[EventPerformanceResponse]:
    """Return POS/weather performance rows for event comparison."""

    performances = query.execute(
        business_unit_id=business_unit_id,
        status=status,
        is_active=is_active,
        starts_from=starts_from,
        starts_to=starts_to,
        limit=limit,
    )
    return [EventPerformanceResponse.model_validate(item) for item in performances]


@router.get("/{event_id}/performance", response_model=EventPerformanceResponse)
def get_event_performance(
    event_id: uuid.UUID,
    query: Annotated[GetEventPerformanceQuery, Depends(get_event_performance_query)],
) -> EventPerformanceResponse:
    """Return POS and weather performance for one event time window."""

    try:
        performance = query.execute(event_id)
    except EventPerformanceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return EventPerformanceResponse.model_validate(performance)


@router.get(
    "/{event_id}/ticket-actual",
    response_model=EventTicketActualResponse | None,
)
def get_event_ticket_actual(
    event_id: uuid.UUID,
    query: Annotated[
        GetEventTicketActualQuery,
        Depends(get_event_ticket_actual_query),
    ],
) -> EventTicketActualResponse | None:
    """Return ticket-system actuals attached to one event."""

    try:
        actual = query.execute(event_id=event_id)
    except EventNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if actual is None:
        return None
    return EventTicketActualResponse.model_validate(actual)


@router.put("/{event_id}/ticket-actual", response_model=EventTicketActualResponse)
def upsert_event_ticket_actual(
    event_id: uuid.UUID,
    payload: EventTicketActualRequest,
    command: Annotated[
        UpsertEventTicketActualCommand,
        Depends(get_upsert_event_ticket_actual_command),
    ],
) -> EventTicketActualResponse:
    """Create or update ticket-system actuals attached to one event."""

    try:
        actual = command.execute(event_id=event_id, **payload.model_dump())
    except EventNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EventTicketActualValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return EventTicketActualResponse.model_validate(actual)


@router.post(
    "/{event_id}/weather/ensure-coverage",
    response_model=EventWeatherCoverageResponse,
    status_code=status.HTTP_201_CREATED,
)
def ensure_event_weather_coverage(
    event_id: uuid.UUID,
    command: Annotated[
        EnsureEventWeatherCoverageCommand,
        Depends(get_ensure_event_weather_coverage_command),
    ],
) -> EventWeatherCoverageResponse:
    """Prepare shared Szolnok weather cache for one event time window."""

    try:
        result = command.execute(event_id=event_id)
    except EventNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except WeatherValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return EventWeatherCoverageResponse.model_validate(result)


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: EventCreateRequest,
    command: Annotated[CreateEventCommand, Depends(get_create_event_command)],
) -> EventResponse:
    """Create one event planning record."""

    try:
        event = command.execute(**payload.model_dump())
    except EventBusinessUnitNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EventLocationMismatchError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except EventValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return EventResponse.model_validate(event)


@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: uuid.UUID,
    payload: EventCreateRequest,
    command: Annotated[UpdateEventCommand, Depends(get_update_event_command)],
) -> EventResponse:
    """Update one event planning record."""

    try:
        event = command.execute(event_id, **payload.model_dump())
    except EventBusinessUnitNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EventNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (EventLocationMismatchError, EventValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return EventResponse.model_validate(event)


@router.delete("/{event_id}", response_model=EventResponse)
def archive_event(
    event_id: uuid.UUID,
    command: Annotated[ArchiveEventCommand, Depends(get_archive_event_command)],
) -> EventResponse:
    """Archive one event planning record."""

    try:
        event = command.execute(event_id)
    except EventNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return EventResponse.model_validate(event)
