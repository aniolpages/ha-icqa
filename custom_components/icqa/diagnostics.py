"""Diagnostics support for ICQA Catalunya."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .const import CONF_STATION_ID, DOMAIN, ICQA_API_URL
from .coordinator import ICQADataUpdateCoordinator

TO_REDACT: list[str] = []


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: ICQADataUpdateCoordinator = entry.runtime_data
    return _build_diagnostics(entry, coordinator)


async def async_get_device_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device: DeviceEntry,
) -> dict[str, Any]:
    """Return diagnostics for a station device."""
    coordinator: ICQADataUpdateCoordinator = entry.runtime_data
    station = coordinator.data
    if (DOMAIN, station.id) not in device.identifiers:
        return {}
    return _build_diagnostics(entry, coordinator)


def _build_diagnostics(
    entry: ConfigEntry,
    coordinator: ICQADataUpdateCoordinator,
) -> dict[str, Any]:
    """Build a diagnostics payload."""
    station = coordinator.data
    payload_generated_at = (
        coordinator.last_payload.generated_at.isoformat()
        if coordinator.last_payload and coordinator.last_payload.generated_at
        else None
    )
    return {
        "entry": async_redact_data(
            {
                "entry_id": entry.entry_id,
                "title": entry.title,
                "station_id": entry.data.get(CONF_STATION_ID),
            },
            TO_REDACT,
        ),
        "api": {
            "url": ICQA_API_URL,
            "update_interval_minutes": 30,
            "last_update_success": coordinator.last_update_success,
            "payload_generated_at": payload_generated_at,
        },
        "station": station.as_dict(),
    }
