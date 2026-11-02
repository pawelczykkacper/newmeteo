"""Sensor platform for Meteo.pl Meteogram."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MeteoPlCoordinator
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the meteogram sensor."""
    coordinator: MeteoPlCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MeteoPlSensor(coordinator, entry)])


class MeteoPlSensor(CoordinatorEntity[MeteoPlCoordinator], SensorEntity):
    """Show the current model temperature and meteogram as its entity picture."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "°C"
    _attr_icon = "mdi:weather-partly-cloudy"

    def __init__(self, coordinator: MeteoPlCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = entry.entry_id
        self._attr_name = "Meteogram"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "meteo.pl / ICM UW",
            "configuration_url": "https://app.meteo.pl",
        }

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("temperature")

    @property
    def entity_picture(self) -> str | None:
        return self.coordinator.data.get("image_url")

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "model": "UM4 60 h",
            "source": "meteo.pl / ICM UW",
            "forecast_start": self.coordinator.data.get("forecast", {}).get("fstart"),
            "latitude": self.coordinator.entry.data["latitude"],
            "longitude": self.coordinator.entry.data["longitude"],
        }
