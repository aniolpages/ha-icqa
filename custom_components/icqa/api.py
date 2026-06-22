"""Async API client for the ICQA Catalunya endpoint."""

from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import ICQA_API_URL, REQUEST_TIMEOUT
from .models import ICQAData, parse_icqa_payload


class ICQAApiError(Exception):
    """Base exception for ICQA API failures."""


class ICQAClient:
    """Client for the public ICQA air-quality API."""

    def __init__(self, session: ClientSession) -> None:
        """Initialize the client."""
        self._session = session

    async def async_get_data(self) -> ICQAData:
        """Fetch and parse the latest ICQA payload."""
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self._session.get(ICQA_API_URL)
                response.raise_for_status()
                payload: dict[str, Any] = await response.json(content_type=None)
        except (TimeoutError, ClientResponseError, ClientError, ValueError) as err:
            raise ICQAApiError("No s'han pogut obtenir les dades de l'ICQA") from err

        return parse_icqa_payload(payload)
