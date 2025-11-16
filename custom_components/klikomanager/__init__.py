"""Init-bestand voor de Klikomanager Home Assistant integratie."""

from __future__ import annotations

from datetime import timedelta, datetime, time
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .api import (
    async_login_with_password,
    async_get_waste_calendar,
    KlikomanagerApiError,
    KlikomanagerAuthError,
)
from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_CARD_NUMBER,
    CONF_PASSWORD,
    CONF_HOST,
    CONF_CLIENT_NAME,
    CONF_APP,
    CONF_TARGET_CALENDAR,
    CONF_SYNCED_EVENTS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up de Klikomanager integratie via YAML (niet gebruikt)."""
    # We ondersteunen alleen config entries (UI-configuratie).
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Klikomanager vanuit een config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = KlikomanagerDataUpdateCoordinator(hass=hass, entry=entry)

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:  # noqa: BLE001
        raise ConfigEntryNotReady(f"Kon Klikomanager data niet ophalen: {err}") from err

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Verwijder een config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


class KlikomanagerDataUpdateCoordinator(DataUpdateCoordinator[list]):
    """Coordinator die de data van Klikomanager ophaalt."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialiseer de coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Klikomanager afvalkalender",
            # Eenmaal per dag verversen is voldoende voor een afvalkalender.
            update_interval=timedelta(days=1),
        )
        self.entry = entry
        # Houd bij welke events we al naar een externe kalender hebben geschreven.
        synced_from_options = entry.options.get(CONF_SYNCED_EVENTS, [])
        self._synced_event_keys: set[tuple[str, int]] = {
            (str_key.split("|")[0], int(str_key.split("|")[1]))
            for str_key in synced_from_options
            if "|" in str_key
        }

    async def _async_update_data(self) -> list:
        """Haal de laatste afvalkalender-data op van Klikomanager.

        Werkwijze:
        - log in met kaartnummer + wachtwoord → short-lived token
        - haal vervolgens de waste calendar op met die token
        - zet de data om naar een lijst met calendar-events
        - schrijf optioneel events weg naar een externe kalender
        """
        data = self.entry.data
        card_number: str = data[CONF_CARD_NUMBER]
        password: str = data[CONF_PASSWORD]
        host: str = data[CONF_HOST]
        client_name: str = data[CONF_CLIENT_NAME]
        app: str = data[CONF_APP]

        try:
            # 1. Login om een verse token te krijgen
            login_result = await async_login_with_password(
                self.hass,
                host=host,
                card_number=card_number,
                password=password,
                client_name=client_name,
                app=app,
            )
            token: str = login_result["token"]

            # 2. Haal de afvalkalender op
            calendar_result = await async_get_waste_calendar(
                self.hass,
                host=host,
                token=token,
                client_name=client_name,
                app=app,
            )

            dates = calendar_result.get("dates", {}) or {}
            fractions = calendar_result.get("fractions", []) or []

            fraction_name_by_id: dict[int, str] = {
                int(f["id"]): str(f.get("name") or f["id"]) for f in fractions
            }

            events: list[dict] = []

            for date_str, entries in dates.items():
                # date_str is "YYYY-MM-DD"
                try:
                    day = datetime.fromisoformat(date_str).date()
                except ValueError:
                    _LOGGER.warning("Ongeldige datum in Klikomanager-data: %s", date_str)
                    continue

                start_dt = datetime.combine(day, time(6, 0))
                end_dt = datetime.combine(day, time(9, 0))

                for entry in entries:
                    # entry is [fractionId, 0]
                    if not entry:
                        continue
                    fraction_id = int(entry[0])
                    fraction_name = fraction_name_by_id.get(
                        fraction_id, f"Fractie {fraction_id}"
                    )

                    events.append(
                        {
                            "summary": fraction_name,
                            "start": start_dt,
                            "end": end_dt,
                            "fraction_id": fraction_id,
                            "fraction_name": fraction_name,
                        }
                    )

            # Schrijf optioneel events weg naar een gekozen kalender-entity
            await self._async_sync_to_target_calendar(events)

            return events

        except (KlikomanagerApiError, KlikomanagerAuthError) as err:
            raise UpdateFailed(f"Fout bij communiceren met Klikomanager: {err}") from err
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Onbekende fout bij ophalen Klikomanager-data: {err}") from err

    async def _async_sync_to_target_calendar(self, events: list[dict]) -> None:
        """Schrijf events weg naar een externe kalender indien geconfigureerd.

        We beperken dubbele creaties binnen dezelfde HA-runtime met een interne set.
        """
        target_calendar: str | None = self.entry.options.get(CONF_TARGET_CALENDAR) or self.entry.data.get(CONF_TARGET_CALENDAR)
        if not target_calendar:
            return

        if not events:
            return

        now = dt_util.utcnow()
        horizon = now + timedelta(days=60)

        new_keys: set[tuple[str, int]] = set()

        for ev in events:
            start: datetime = dt_util.as_utc(ev["start"])
            end: datetime = dt_util.as_utc(ev["end"])

            # Alleen toekomstige events binnen een horizon synchroniseren
            if end < now or start > horizon:
                continue

            key = (start.date().isoformat(), int(ev["fraction_id"]))
            if key in self._synced_event_keys:
                continue
            self._synced_event_keys.add(key)
            new_keys.add(key)

            summary = ev["summary"]
            description = f"Klikomanager: {ev['fraction_name']}"

            start_local = dt_util.as_local(start).isoformat()
            end_local = dt_util.as_local(end).isoformat()

            _LOGGER.debug(
                "Maak event in %s voor %s (%s)",
                target_calendar,
                start_local,
                summary,
            )

            await self.hass.services.async_call(
                "calendar",
                "create_event",
                {
                    "entity_id": target_calendar,
                    "summary": summary,
                    "description": description,
                    "start_date_time": start_local,
                    "end_date_time": end_local,
                },
                blocking=False,
            )

        # Bewaar de nieuwe keys in de config entry options zodat we na een
        # herstart geen dubbele events meer aanmaken.
        if new_keys:
            all_keys = {*(self._synced_event_keys)}
            keys_as_str = sorted(f"{d}|{fid}" for (d, fid) in all_keys)
            new_options = {
                **self.entry.options,
                CONF_SYNCED_EVENTS: keys_as_str,
            }
            self.hass.config_entries.async_update_entry(
                self.entry,
                options=new_options,
            )


