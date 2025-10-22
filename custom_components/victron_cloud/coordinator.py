"""Data update coordinator for Victron Cloud."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import VictronApiAuthError, VictronApiClient, VictronApiError
from .const import (
    CONF_DEVICE_INSTANCE,
    CONF_INSTALLATION_ID,
    CONF_INSTALLATION_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class VictronDataUpdateCoordinator(DataUpdateCoordinator[dict[int, float | int | str | None]]):
    """Coordinator responsible for polling the Victron API."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api_client: VictronApiClient,
        attribute_ids: list[int],
        update_interval: timedelta | None = None,
    ) -> None:
        self.api_client = api_client
        self.entry = entry
        self.installation_id = entry.data[CONF_INSTALLATION_ID]
        self.installation_name = entry.data.get(CONF_INSTALLATION_NAME, "Victron Installation")
        self.device_instance = entry.data.get(CONF_DEVICE_INSTANCE, 0)
        self.attribute_ids = attribute_ids

        interval = update_interval or DEFAULT_SCAN_INTERVAL

        super().__init__(
            hass,
            _LOGGER,
            name=f"Victron Cloud ({self.installation_name})",
            update_interval=interval,
        )

    async def _async_update_data(self) -> dict[int, float | int | str | None]:
        """Fetch data from the Victron API."""

        try:
            return await self.api_client.async_get_latest_values(
                self.installation_id, self.attribute_ids, self.device_instance
            )
        except VictronApiAuthError as err:
            raise ConfigEntryAuthFailed("Victron authentication failed") from err
        except VictronApiError as err:
            raise UpdateFailed(f"Error updating Victron data: {err}") from err
