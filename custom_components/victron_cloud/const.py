"""Constants for the Victron Cloud integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "victron_cloud"
PLATFORMS: list[Platform] = [Platform.SENSOR]

CONF_API_TOKEN = "api_token"
CONF_INSTALLATION_ID = "installation_id"
CONF_INSTALLATION_NAME = "installation_name"
CONF_DEVICE_INSTANCE = "device_instance"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_SENSORS = "sensors"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=1)
MIN_SCAN_INTERVAL = 30
DEFAULT_DEVICE_INSTANCE = 0

API_BASE_URL = "https://vrmapi.victronenergy.com/v2"

ERROR_INVALID_AUTH = "invalid_auth"
ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_NO_INSTALLATIONS = "no_installations"
