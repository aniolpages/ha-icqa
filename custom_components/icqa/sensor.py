"""Sensor platform for ICQA Catalunya."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER,
    EntityCategory,
    UnitOfLength,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_LEGACY_QUALITY,
    ATTR_UPDATED_AT,
    DOMAIN,
    ICQA_INFO_URL,
    MANUFACTURER,
    MODEL,
    NO_MEASUREMENT_STATES,
    QUALITY_OPTIONS,
)
from .coordinator import ICQADataUpdateCoordinator
from .models import ContaminantReading, Station

POLLUTANT_ICONS = {
    "C6H6": "mdi:molecule",
    "CO": "mdi:molecule",
    "H2S": "mdi:molecule",
    "NO2": "mdi:molecule",
    "O3": "mdi:molecule",
    "PM10": "mdi:weather-dust",
    "PM2.5": "mdi:weather-dust",
    "SO2": "mdi:molecule",
}

POLLUTANT_DEVICE_CLASSES = {
    "C6H6": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
    "CO": SensorDeviceClass.CO,
    "NO2": SensorDeviceClass.NITROGEN_DIOXIDE,
    "O3": SensorDeviceClass.OZONE,
    "PM10": SensorDeviceClass.PM10,
    "PM2.5": SensorDeviceClass.PM25,
    "SO2": SensorDeviceClass.SULPHUR_DIOXIDE,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ICQA Catalunya sensors from a config entry."""
    coordinator: ICQADataUpdateCoordinator = entry.runtime_data
    station = coordinator.data

    entities: list[SensorEntity] = [
        ICQAStationQualitySensor(coordinator),
        ICQALastUpdateSensor(coordinator),
    ]

    if station.installed_on is not None:
        entities.append(ICQAInstallationDateSensor(coordinator))
    if station.altitude is not None or station.elevation is not None:
        entities.append(ICQAAltitudeSensor(coordinator))

    entities.extend(
        ICQAPollutantSensor(coordinator, reading)
        for reading in _station_sensor_readings(station)
    )

    async_add_entities(entities)


class ICQAEntity(CoordinatorEntity[ICQADataUpdateCoordinator]):
    """Base ICQA entity."""

    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for the station."""
        station = self.coordinator.data
        device_info: DeviceInfo = {
            "identifiers": {(DOMAIN, station.id)},
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "name": station.name,
            "configuration_url": ICQA_INFO_URL,
        }
        if station.locality:
            device_info["suggested_area"] = station.locality
        return device_info


class ICQAStationQualitySensor(ICQAEntity, SensorEntity):
    """General station air quality sensor."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_icon = "mdi:air-filter"
    _attr_options = QUALITY_OPTIONS
    _attr_translation_key = "station_quality"

    def __init__(self, coordinator: ICQADataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.station_id}_quality"

    @property
    def native_value(self) -> str | None:
        """Return the station quality state."""
        return self.coordinator.data.quality

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return station metadata as attributes."""
        station = self.coordinator.data
        attrs = station.station_attributes()
        attrs[ATTR_LEGACY_QUALITY] = station.legacy_quality
        return attrs


class ICQAPollutantSensor(ICQAEntity, SensorEntity):
    """Sensor for a pollutant concentration."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_translation_key = "pollutant_concentration"

    def __init__(
        self,
        coordinator: ICQADataUpdateCoordinator,
        reading: ContaminantReading,
    ) -> None:
        """Initialize the pollutant sensor."""
        super().__init__(coordinator)
        self._abbr = reading.abbr
        self._name = reading.name or reading.abbr
        self._attr_device_class = POLLUTANT_DEVICE_CLASSES.get(reading.abbr)
        self._attr_icon = POLLUTANT_ICONS.get(reading.abbr, "mdi:molecule")
        self._attr_native_unit_of_measurement = _home_assistant_unit(reading.unit)
        self._attr_translation_placeholders = {"pollutant": self._name}
        self._attr_unique_id = (
            f"{coordinator.station_id}_{reading.unique_key}_concentration"
        )

    @property
    def available(self) -> bool:
        """Return whether this pollutant currently has a measurement."""
        reading = self._current_reading
        return (
            super().available
            and reading is not None
            and reading.value is not None
            and reading.quality not in NO_MEASUREMENT_STATES
        )

    @property
    def native_value(self) -> float | None:
        """Return the pollutant concentration."""
        reading = self._current_reading
        return reading.value if reading else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return pollutant metadata."""
        reading = self._current_reading
        if reading is None:
            return {}
        attrs: dict[str, Any] = {
            "contaminant": reading.abbr,
            "nom_contaminant": reading.name,
            "qualitat": reading.quality,
            "qualitat_original": reading.legacy_quality,
            "valor_original": reading.raw_value,
        }
        if self.coordinator.data.updated_at:
            attrs[ATTR_UPDATED_AT] = self.coordinator.data.updated_at.isoformat()
        return {key: value for key, value in attrs.items() if value is not None}

    @property
    def _current_reading(self) -> ContaminantReading | None:
        """Return the current reading matching this entity."""
        return self.coordinator.data.readings.get(self._abbr)


class ICQALastUpdateSensor(ICQAEntity, SensorEntity):
    """Diagnostic sensor for the station update time."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:clock-outline"
    _attr_translation_key = "last_update"

    def __init__(self, coordinator: ICQADataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.station_id}_last_update"

    @property
    def native_value(self) -> Any:
        """Return the station update timestamp."""
        return self.coordinator.data.updated_at


class ICQAInstallationDateSensor(ICQAEntity, SensorEntity):
    """Diagnostic sensor for the station installation date."""

    _attr_device_class = SensorDeviceClass.DATE
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:calendar-start"
    _attr_translation_key = "installation_date"

    def __init__(self, coordinator: ICQADataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.station_id}_installation_date"

    @property
    def native_value(self) -> Any:
        """Return the station installation date."""
        return self.coordinator.data.installed_on


class ICQAAltitudeSensor(ICQAEntity, SensorEntity):
    """Diagnostic sensor for the station altitude."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:elevation-rise"
    _attr_native_unit_of_measurement = UnitOfLength.METERS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_translation_key = "altitude"

    def __init__(self, coordinator: ICQADataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.station_id}_altitude"

    @property
    def native_value(self) -> float | None:
        """Return the station altitude."""
        station = self.coordinator.data
        return station.altitude if station.altitude is not None else station.elevation


def _station_sensor_readings(station: Station) -> Iterable[ContaminantReading]:
    """Return readings that should be represented as measurement sensors."""
    measured_abbrs = station.measured_abbrs
    for reading in station.sorted_readings:
        if reading.abbr in measured_abbrs or reading.value is not None:
            yield reading


def _home_assistant_unit(unit: str | None) -> str | None:
    """Return a Home Assistant concentration unit."""
    if unit is None:
        return None
    normalized = unit.lower().replace("³", "3")
    if normalized == "µg/m3":
        return CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    if normalized == "mg/m3":
        return CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER
    return unit
