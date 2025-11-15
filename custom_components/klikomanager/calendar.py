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
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Retourneer events in de gevraagde periode.

        Nu nog op basis van dummy-data uit de coordinator.
        """
        events: list[CalendarEvent] = []

        for item in self.coordinator.data or []:
            start: datetime = item["start"]
            end: datetime = item["end"]

            # Filter op de gevraagde periode
            if end < start_date or start > end_date:
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


