"""Config flow voor de Klikomanager integratie."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .api import (
    KlikomanagerApiError,
    KlikomanagerAuthError,
    async_login_with_password,
)
from .const import (
    DOMAIN,
    CONF_CARD_NUMBER,
    CONF_PASSWORD,
    CONF_HOST,
    CONF_CLIENT_NAME,
    CONF_APP,
    DEFAULT_HOST,
    DEFAULT_CLIENT_NAME,
    DEFAULT_APP,
)


async def _async_validate_input(
    hass: HomeAssistant,
    data: dict,
) -> dict:
    """Valideer de gebruikersinvoer via een login-call naar Klikomanager."""
    card_number: str = data[CONF_CARD_NUMBER]
    password: str = data[CONF_PASSWORD]

    # Voor nu gebruiken we de standaard host/client/app voor Uithoorn.
    host: str = DEFAULT_HOST
    client_name: str = DEFAULT_CLIENT_NAME
    app: str = DEFAULT_APP

    result = await async_login_with_password(
        hass,
        host=host,
        card_number=card_number,
        password=password,
        client_name=client_name,
        app=app,
    )

    config = result.get("config", {}) or {}
    card_details = config.get("cardDetails", {}) or {}
    address = card_details.get("address", {}) or {}

    street = address.get("street")
    street_number = address.get("streetNumber")
    zip_code = address.get("zipCode")

    # Mooie titel op basis van adres, valt terug op kaartnummer.
    address_parts = [p for p in (street, street_number, zip_code) if p]
    if address_parts:
        title = "Klikomanager (" + ", ".join(address_parts) + ")"
    else:
        title = f"Klikomanager kaart {card_number}"

    return {
        "title": title,
        "host": host,
        "client_name": client_name,
        "app": app,
    }


class KlikomanagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow voor Klikomanager."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Afhandelen van de eerste stap."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await _async_validate_input(self.hass, user_input)
            except KlikomanagerAuthError:
                errors["base"] = "invalid_auth"
            except KlikomanagerApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    f"{info['host']}_{user_input[CONF_CARD_NUMBER]}"
                )
                self._abort_if_unique_id_configured()

                data = {
                    CONF_CARD_NUMBER: user_input[CONF_CARD_NUMBER],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                    CONF_HOST: info["host"],
                    CONF_CLIENT_NAME: info["client_name"],
                    CONF_APP: info["app"],
                }

                return self.async_create_entry(title=info["title"], data=data)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_CARD_NUMBER): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )


