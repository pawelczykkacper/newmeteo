"""Meteo.pl meteogram integration."""

from __future__ import annotations

import logging

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_BASE, DOMAIN, MODEL, PLATFORMS, UPDATE_INTERVAL
from .image import render_meteogram

_LOGGER = logging.getLogger(__name__)


class MeteoPlCoordinator(DataUpdateCoordinator[dict]):
    """Fetch the latest meteo.pl forecast and build its image."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"Meteo.pl {entry.title}",
            update_interval=UPDATE_INTERVAL,
        )
        self.entry = entry
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict:
        try:
            import aiohttp

            timeout = aiohttp.ClientTimeout(total=30)
            async with self.session.get(
                f"{API_BASE}/meteorograms/available", timeout=timeout
            ) as response:
                response.raise_for_status()
                available = await response.json()

            dates = available.get(MODEL, [])
            if not dates:
                raise UpdateFailed("Meteo.pl nie udostępnia obecnie nowego przebiegu UM4")

            payload = {
                "point": {
                    "lat": self.entry.data["latitude"],
                    "lon": self.entry.data["longitude"],
                },
                "date": dates[-1],
            }
            async with self.session.post(
                f"{API_BASE}/meteorograms/{MODEL}", json=payload, timeout=timeout
            ) as response:
                response.raise_for_status()
                forecast = await response.json()

            image = await self.hass.async_add_executor_job(
                render_meteogram, forecast, self.entry.title
            )
            image_path = self.hass.config.path(
                "www", f"meteo_pl_{self.entry.entry_id}.png"
            )
            await self.hass.async_add_executor_job(_write_image, image_path, image)

            data = forecast.get("data", {})
            temperature = _first_value(data, "airtmp_point")
            return {
                "temperature": temperature,
                "forecast": forecast,
                "image_url": f"/local/meteo_pl_{self.entry.entry_id}.png",
            }
        except UpdateFailed:
            raise
        except (ClientError, TimeoutError, ValueError, KeyError) as err:
            raise UpdateFailed(f"Błąd pobierania meteogramu z meteo.pl: {err}") from err


def _first_value(data: dict, field: str) -> float | None:
    values = data.get(field, {}).get("data", [])
    return values[0] if values else None


def _write_image(path: str, image: bytes) -> None:
    from pathlib import Path

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(image)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configured location."""
    coordinator = MeteoPlCoordinator(hass, entry)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a configured location."""
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        return True
    return False
