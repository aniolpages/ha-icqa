"""Config flow for ICQA Catalunya."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ICQAApiError, ICQAClient
from .const import CONF_STATION_ID, DOMAIN
from .models import ICQAData, Station


class ICQAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an ICQA Catalunya config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._data: ICQAData | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Let the user choose an ICQA station."""
        errors: dict[str, str] = {}

        if self._data is None:
            try:
                self._data = await self._async_fetch_data()
            except ICQAApiError:
                return self.async_abort(reason="cannot_connect")

        if not self._data.stations:
            return self.async_abort(reason="no_stations")

        if user_input is not None:
            station_id = user_input[CONF_STATION_ID]
            station = self._data.stations.get(station_id)
            if station is None:
                errors["base"] = "invalid_station"
            else:
                await self.async_set_unique_id(station.id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=station.name,
                    data={CONF_STATION_ID: station.id},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATION_ID): vol.In(
                        _station_options(self._data.stations)
                    )
                }
            ),
            errors=errors,
        )

    async def _async_fetch_data(self) -> ICQAData:
        """Fetch station options from the ICQA endpoint."""
        client = ICQAClient(async_get_clientsession(self.hass))
        return await client.async_get_data()


def _station_options(stations: dict[str, Station]) -> dict[str, str]:
    """Return station options sorted for display in the UI."""
    sorted_stations = sorted(
        stations.values(),
        key=lambda station: (
            station.locality or "",
            station.name,
            station.id,
        ),
    )
    return {station.id: _station_label(station) for station in sorted_stations}


def _station_label(station: Station) -> str:
    """Return a user-friendly station label."""
    details: list[str] = []
    if station.locality and station.locality.lower() not in station.name.lower():
        details.append(station.locality)
    if station.zone_name:
        details.append(station.zone_name)

    suffix = f" - {', '.join(details)}" if details else ""
    return f"{station.name}{suffix} ({station.id})"
