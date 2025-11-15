"""Constanten voor de Klikomanager Home Assistant integratie."""

from __future__ import annotations

DOMAIN = "klikomanager"

# Oorspronkelijke adresvelden (mogelijk later weer nodig)
CONF_POSTCODE = "postcode"
CONF_HOUSE_NUMBER = "house_number"
CONF_HOUSE_NUMBER_SUFFIX = "house_number_suffix"

# Loginvelden voor Klikomanager
CONF_CARD_NUMBER = "card_number"
CONF_PASSWORD = "password"

# API/host-gerelateerde opties
CONF_HOST = "host"
CONF_CLIENT_NAME = "client_name"
CONF_APP = "app"
# We slaan de token niet persistent op omdat deze korte tijd geldig is.
CONF_TOKEN = "token"

DEFAULT_NAME = "Klikomanager Afvalkalender"

# Standaardwaarden afgeleid uit de Tempfile (gemeente Uithoorn)
DEFAULT_HOST = "cp-uithoorn.klikocontainermanager.com"
DEFAULT_CLIENT_NAME = "uithoorn"
DEFAULT_APP = "cp-uithoorn.kcm.com"

API_LOGIN_PATH = "/MyKliko/loginWithPassword"
API_WASTE_CALENDAR_PATH = "/MyKliko/getMyWasteCalendar"

PLATFORMS: list[str] = ["calendar"]

