"""Eenvoudige API-client voor Klikomanager."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_LOGIN_PATH, API_WASTE_CALENDAR_PATH

_LOGGER = logging.getLogger(__name__)


class KlikomanagerApiError(Exception):
    """Algemene fout bij communiceren met Klikomanager."""


class KlikomanagerAuthError(KlikomanagerApiError):
    """Authenticatiefout bij Klikomanager."""


async def async_login_with_password(
    hass: HomeAssistant,
    *,
    host: str,
    card_number: str,
    password: str,
    client_name: str,
    app: str,
) -> dict[str, Any]:
    """Voer een loginWithPassword-call uit en retourneer de JSON-respons.

    Verwacht een structuur zoals vastgelegd in de Tempfile:
    - token onder `token`
    - configuratie onder `config`
    """
    session = async_get_clientsession(hass)
    url = f"https://{host}{API_LOGIN_PATH}"

    payload = {
        "cardNumber": card_number,
        "password": password,
        "clientName": client_name,
        "app": app,
        "deviceId": "",
    }

    try:
        async with session.post(url, json=payload, timeout=15) as resp:
            data: dict[str, Any] = await resp.json()
    except ClientError as err:
        raise KlikomanagerApiError(
            f"Kon geen verbinding maken met Klikomanager: {err}"
        ) from err

    if not data.get("success"):
        # Geen succesvolle login
        raise KlikomanagerAuthError("Login bij Klikomanager mislukt (success = false)")

    if "token" not in data:
        raise KlikomanagerApiError("Respons van Klikomanager bevat geen token")

    # Log geen token/wachtwoord!
    _LOGGER.debug(
        "Succesvol ingelogd bij Klikomanager voor kaartnummer eindigend op %s",
        str(card_number)[-4:],
    )

    return data


async def async_get_waste_calendar(
    hass: HomeAssistant,
    *,
    host: str,
    token: str,
    client_name: str,
    app: str,
) -> dict[str, Any]:
    """Haal de afvalkalender op via getMyWasteCalendar."""
    session = async_get_clientsession(hass)
    url = f"https://{host}{API_WASTE_CALENDAR_PATH}"

    payload = {
        "token": token,
        "clientName": client_name,
        "app": app,
        "deviceId": "",
    }

    try:
        async with session.post(url, json=payload, timeout=15) as resp:
            data: dict[str, Any] = await resp.json()
    except ClientError as err:
        raise KlikomanagerApiError(
            f"Kon geen verbinding maken met Klikomanager (waste calendar): {err}"
        ) from err

    if "dates" not in data or "fractions" not in data:
        raise KlikomanagerApiError(
            "Respons van Klikomanager bevat geen geldige kalenderdata"
        )

    return data



