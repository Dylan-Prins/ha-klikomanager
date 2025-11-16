"""Config flow voor de Klikomanager integratie."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

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
    CONF_TARGET_CALENDAR,
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

                data: dict = {
                    CONF_CARD_NUMBER: user_input[CONF_CARD_NUMBER],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                    CONF_HOST: info["host"],
                    CONF_CLIENT_NAME: info["client_name"],
                    CONF_APP: info["app"],
                }

                # Sla een eventuele gekozen doelkalender ook direct op
                target_calendar = user_input.get(CONF_TARGET_CALENDAR)
                if target_calendar:
                    data[CONF_TARGET_CALENDAR] = target_calendar

                return self.async_create_entry(title=info["title"], data=data)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_CARD_NUMBER): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_TARGET_CALENDAR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="calendar")
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )


class KlikomanagerOptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow voor Klikomanager."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialiseer de options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict | None = None,
    ) -> FlowResult:
        """Behandel de options-flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_target = self.config_entry.options.get(CONF_TARGET_CALENDAR, "")

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_TARGET_CALENDAR,
                    default=current_target,
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="calendar")
                )
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )


async def async_get_options_flow(
    config_entry: config_entries.ConfigEntry,
) -> KlikomanagerOptionsFlowHandler:
    """Return the options flow handler."""
    return KlikomanagerOptionsFlowHandler(config_entry)


