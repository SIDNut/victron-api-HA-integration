"""The Victron Cloud integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .api import VictronApiClient
from .const import (
    CONF_API_TOKEN,
    CONF_SENSORS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import VictronDataUpdateCoordinator
from .models import VictronConfigEntry, VictronRuntimeData
from .sensors import DEFAULT_SENSOR_KEYS, SENSOR_MAP

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Victron Cloud component."""

    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: VictronConfigEntry) -> bool:
    """Set up Victron Cloud from a config entry."""

    api_token: str = entry.data[CONF_API_TOKEN]
    api_client = VictronApiClient(hass, api_token)

    selected_keys = entry.options.get(CONF_SENSORS, DEFAULT_SENSOR_KEYS)
    descriptions = [SENSOR_MAP[key] for key in selected_keys if key in SENSOR_MAP]
    if not descriptions:
        descriptions = [SENSOR_MAP[key] for key in DEFAULT_SENSOR_KEYS]

    _LOGGER.debug("Setting up Victron sensors: %s", [desc.key for desc in descriptions])

    attribute_ids: list[int] = sorted(
        {
            *[desc.attribute_id for desc in descriptions if desc.attribute_id is not None],
            *[attr_id for desc in descriptions for attr_id in desc.requires],
        }
    )

    update_interval = entry.options.get(CONF_SCAN_INTERVAL)
    if isinstance(update_interval, int):
        scan_interval = timedelta(seconds=update_interval)
    elif isinstance(update_interval, timedelta):
        scan_interval = update_interval
    else:
        scan_interval = DEFAULT_SCAN_INTERVAL

    coordinator = VictronDataUpdateCoordinator(
        hass=hass,
        entry=entry,
        api_client=api_client,
        attribute_ids=attribute_ids,
        update_interval=scan_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = VictronRuntimeData(
        coordinator=coordinator,
        descriptions=tuple(descriptions),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: VictronConfigEntry) -> bool:
    """Unload a Victron Cloud config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry.runtime_data = None
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update by reloading the entry."""

    await hass.config_entries.async_reload(entry.entry_id)
