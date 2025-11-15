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
            update_interval=timedelta(hours=6),
        )
        self.entry = entry

    async def _async_update_data(self) -> list:
        """Haal de laatste afvalkalender-data op van Klikomanager.

        Werkwijze:
        - log in met kaartnummer + wachtwoord → short-lived token
        - haal vervolgens de waste calendar op met die token
        - zet de data om naar een lijst met calendar-events
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

            return events

        except (KlikomanagerApiError, KlikomanagerAuthError) as err:
            raise UpdateFailed(f"Fout bij communiceren met Klikomanager: {err}") from err
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Onbekende fout bij ophalen Klikomanager-data: {err}") from err


