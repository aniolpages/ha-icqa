"""Data update coordinator for ICQA Catalunya."""

from __future__ import annotations

from datetime import UTC, datetime
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ICQAApiError, ICQAClient
from .const import DOMAIN, SCAN_INTERVAL
from .models import ICQAData, Station

_LOGGER = logging.getLogger(__name__)


class ICQADataUpdateCoordinator(DataUpdateCoordinator[Station]):
    """Coordinator that fetches one ICQA station from the shared endpoint."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: ICQAClient,
        station_id: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{station_id}",
            update_interval=SCAN_INTERVAL,
            always_update=True,
        )
        self.client = client
        self.station_id = station_id
        self.last_payload: ICQAData | None = None
        self.last_fetch_at: datetime | None = None

    async def _async_update_data(self) -> Station:
        """Fetch the latest data for the configured station."""
        try:
            payload = await self.client.async_get_data()
        except ICQAApiError as err:
            raise UpdateFailed(str(err)) from err

        self.last_payload = payload
        station = payload.stations.get(self.station_id)
        if station is None:
            raise UpdateFailed(
                f"L'estació ICQA {self.station_id} no apareix a les dades actuals"
            )

        self.last_fetch_at = datetime.now(UTC)
        return station
