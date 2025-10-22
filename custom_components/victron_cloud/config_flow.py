"""Config flow for the Victron Cloud integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_TOKEN
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .api import VictronApiAuthError, VictronApiClient, VictronApiError
from .const import (
    CONF_DEVICE_INSTANCE,
    CONF_INSTALLATION_ID,
    CONF_INSTALLATION_NAME,
    CONF_SCAN_INTERVAL,
    CONF_SENSORS,
    DEFAULT_DEVICE_INSTANCE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ERROR_CANNOT_CONNECT,
    ERROR_INVALID_AUTH,
    ERROR_NO_INSTALLATIONS,
)
from .sensors import DEFAULT_SENSOR_KEYS, SENSOR_MAP

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_API_TOKEN): str})


class VictronConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Victron Cloud."""

    VERSION = 1

    def __init__(self) -> None:
        self._installations: list[dict[str, Any]] = []
        self._api_token: str | None = None

    async def async_step_user(self, user_input: Mapping[str, Any] | None = None) -> FlowResult:
        """Handle the initial step where the user enters the API token."""

        errors: dict[str, str] = {}

        if user_input is not None:
            api_token = user_input[CONF_API_TOKEN].strip()
            client = VictronApiClient(self.hass, api_token)

            try:
                installations = await client.async_get_installations()
            except VictronApiAuthError:
                errors["base"] = ERROR_INVALID_AUTH
            except VictronApiError:
                errors["base"] = ERROR_CANNOT_CONNECT
            else:
                if not installations:
                    errors["base"] = ERROR_NO_INSTALLATIONS
                else:
                    self._installations = installations
                    self._api_token = api_token
                    return await self.async_step_installation()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_installation(self, user_input: Mapping[str, Any] | None = None) -> FlowResult:
        """Allow the user to select the installation and provide device instance."""

        assert self._api_token is not None

        installation_options: dict[str, str] = {}
        for installation in self._installations:
            installation_id = installation.get("idSite")
            if installation_id is None:
                continue
            name = installation.get("name") or f"Installation {installation_id}"
            installation_options[str(installation_id)] = name

        if not installation_options:
            return self.async_abort(reason=ERROR_NO_INSTALLATIONS)

        errors: dict[str, str] = {}

        if user_input is not None:
            installation_id_raw = user_input.get(CONF_INSTALLATION_ID)
            device_instance = user_input.get(CONF_DEVICE_INSTANCE, DEFAULT_DEVICE_INSTANCE)

            try:
                installation_id = int(installation_id_raw)
            except (TypeError, ValueError):
                errors[CONF_INSTALLATION_ID] = "invalid_installation"
            else:
                await self.async_set_unique_id(str(installation_id))
                self._abort_if_unique_id_configured()

                if isinstance(device_instance, str):
                    try:
                        device_instance = int(device_instance)
                    except ValueError:
                        errors[CONF_DEVICE_INSTANCE] = "invalid_device_instance"
                        device_instance = DEFAULT_DEVICE_INSTANCE

                if not errors:
                    installation_name = installation_options[str(installation_id)]

                    return self.async_create_entry(
                        title=installation_name,
                        data={
                            CONF_API_TOKEN: self._api_token,
                            CONF_INSTALLATION_ID: installation_id,
                            CONF_INSTALLATION_NAME: installation_name,
                            CONF_DEVICE_INSTANCE: device_instance,
                        },
                        options={
                            CONF_SENSORS: DEFAULT_SENSOR_KEYS,
                            CONF_SCAN_INTERVAL: int(DEFAULT_SCAN_INTERVAL.total_seconds()),
                        },
                    )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_INSTALLATION_ID): vol.In(installation_options),
                vol.Required(CONF_DEVICE_INSTANCE, default=DEFAULT_DEVICE_INSTANCE): vol.Coerce(int),
            }
        )

        return self.async_show_form(
            step_id="installation",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "integration_portal": "https://vrm.victronenergy.com/profile/integrations",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return VictronOptionsFlowHandler(config_entry)


class VictronOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for the Victron integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Mapping[str, Any] | None = None) -> FlowResult:
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input: Mapping[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_sensors = user_input.get(CONF_SENSORS)
            if isinstance(selected_sensors, str):
                selected_sensors = [selected_sensors]
            elif isinstance(selected_sensors, (set, tuple)):
                selected_sensors = list(selected_sensors)
            if selected_sensors:
                selected_sensors = [sensor for sensor in selected_sensors if sensor in SENSOR_MAP]
                selected_sensors = list(selected_sensors)
            if not selected_sensors:
                errors[CONF_SENSORS] = "select_sensor"
            else:
                scan_interval = int(user_input[CONF_SCAN_INTERVAL])
                if scan_interval < 30:
                    errors[CONF_SCAN_INTERVAL] = "interval_too_short"
                else:
                    return self.async_create_entry(
                        title="",
                        data={
                            CONF_SENSORS: selected_sensors,
                            CONF_SCAN_INTERVAL: scan_interval,
                        },
                    )

        current_sensors = self.config_entry.options.get(CONF_SENSORS, DEFAULT_SENSOR_KEYS)
        if isinstance(current_sensors, str):
            current_sensors = [current_sensors]
        scan_interval_default = int(
            self.config_entry.options.get(
                CONF_SCAN_INTERVAL, int(DEFAULT_SCAN_INTERVAL.total_seconds())
            )
        )

        sensor_options = [
            {"value": key, "label": description.name}
            for key, description in SENSOR_MAP.items()
        ]

        data_schema = vol.Schema(
            {
                vol.Required(CONF_SENSORS, default=current_sensors): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=sensor_options, multiple=True)
                ),
                vol.Required(CONF_SCAN_INTERVAL, default=scan_interval_default): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=30,
                        max=3600,
                        unit_of_measurement="seconds",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
