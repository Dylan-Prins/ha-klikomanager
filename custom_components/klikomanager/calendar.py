"""Calendar platform voor de Klikomanager integratie."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.calendar import (
    CalendarEntity,
    CalendarEvent,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, DEFAULT_NAME
from . import KlikomanagerDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up de calendar-entity vanuit een config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: KlikomanagerDataUpdateCoordinator = data["coordinator"]

    async_add_entities(
        [
            KlikomanagerCalendarEntity(
                coordinator=coordinator,
                entry=entry,
            )
        ]
    )


class KlikomanagerCalendarEntity(CoordinatorEntity[KlikomanagerDataUpdateCoordinator], CalendarEntity):
    """Calendar entity die ophaaldagen van Klikomanager toont."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KlikomanagerDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialiseer de calendar-entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_name = DEFAULT_NAME

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Retourneer extra attributen."""
        return {
            "source": "klikomanager.com",
        }

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Retourneer events in de gevraagde periode.

        Nu nog op basis van dummy-data uit de coordinator.
        """
        events: list[CalendarEvent] = []

        # Converteer naar UTC met timezone, zoals Home Assistant verwacht
        start_date_utc = dt_util.as_utc(start_date)
        end_date_utc = dt_util.as_utc(end_date)

        for item in self.coordinator.data or []:
            start: datetime = dt_util.as_utc(item["start"])
            end: datetime = dt_util.as_utc(item["end"])

            # Filter op de gevraagde periode
            if end < start_date_utc or start > end_date_utc:
                continue

            events.append(
                CalendarEvent(
                    summary=item.get("summary") or DEFAULT_NAME,
                    start=start,
                    end=end,
                    description=item.get("description"),
                )
            )

        return events

    @property
    def event(self) -> CalendarEvent | None:
        """Retourneer het eerstvolgende event (voor entity-state)."""
        if not self.coordinator.data:
            return None

        now = dt_util.utcnow()
        next_event: CalendarEvent | None = None

        for item in self.coordinator.data:
            start: datetime = dt_util.as_utc(item["start"])
            end: datetime = dt_util.as_utc(item["end"])

            # Alleen toekomstige of lopende events meenemen
            if end < now:
                continue

            candidate = CalendarEvent(
                summary=item.get("summary") or DEFAULT_NAME,
                start=start,
                end=end,
                description=item.get("description"),
            )

            if next_event is None or candidate.start < next_event.start:
                next_event = candidate

        return next_event


