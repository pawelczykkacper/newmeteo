"""Config flow for Meteo.pl Meteogram."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_LOCATION
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, GEOCODING_URL

_LOGGER = logging.getLogger(__name__)


async def _find_location(hass: HomeAssistant, query: str) -> dict[str, Any]:
    """Resolve a place name with the geocoder used by meteo.pl."""
    session = async_get_clientsession(hass)
    async with session.get(
        GEOCODING_URL,
        params={"q": query, "limit": 1, "osm_tag": "place", "lang": "pl"},
        timeout=aiohttp.ClientTimeout(total=15),
    ) as response:
        response.raise_for_status()
        result = await response.json()

    features = result.get("features", [])
    if not features:
        raise ValueError("location_not_found")

    feature = features[0]
    coordinates = feature["geometry"]["coordinates"]
    properties = feature.get("properties", {})
    name = properties.get("name") or query
    locality = properties.get("city") or properties.get("county")
    if locality and locality.lower() != name.lower():
        name = f"{name}, {locality}"
    return {"location": name, "longitude": coordinates[0], "latitude": coordinates[1]}


class MeteoPlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meteo.pl Meteogram."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            query = user_input[CONF_LOCATION].strip()
            try:
                location = await _find_location(self.hass, query)
            except ValueError:
                errors["base"] = "location_not_found"
            except (aiohttp.ClientError, TimeoutError, KeyError, TypeError):
                _LOGGER.exception("Could not resolve location %s", query)
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(
                    f"{location['latitude']:.4f}_{location['longitude']:.4f}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=location["location"], data=location
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_LOCATION): str}),
            errors=errors,
        )
