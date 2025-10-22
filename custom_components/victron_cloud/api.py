"""Client for interacting with the Victron VRM cloud API."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientResponseError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_BASE_URL


class VictronApiError(Exception):
    """Raised when the Victron API returns an unexpected response."""


class VictronApiAuthError(VictronApiError):
    """Raised when authentication with the Victron API fails."""


class VictronApiClient:
    """Simple async client for the Victron VRM API."""

    def __init__(self, hass: HomeAssistant, api_token: str) -> None:
        self._hass = hass
        self._api_token = api_token
        self._session = async_get_clientsession(hass)

    @property
    def headers(self) -> dict[str, str]:
        """Return headers required by the API."""

        return {
            "Content-Type": "application/json",
            "x-authorization": f"Token {self._api_token}",
        }

    async def async_get_installations(self) -> list[dict[str, Any]]:
        """Return the list of installations accessible with this token."""

        url = f"{API_BASE_URL}/installations"
        try:
            async with self._session.get(url, headers=self.headers, raise_for_status=True) as response:
                payload = await response.json()
        except ClientResponseError as err:
            if err.status in (401, 403):
                raise VictronApiAuthError("Invalid API token") from err
            raise VictronApiError(f"Error fetching installations: {err}") from err
        except ClientError as err:
            raise VictronApiError(f"Error communicating with Victron API: {err}") from err

        records = payload.get("records")
        if not isinstance(records, list):
            raise VictronApiError("Unexpected response while listing installations")

        installations: list[dict[str, Any]] = []
        for item in records:
            if not isinstance(item, dict):
                continue
            if "idSite" not in item:
                continue
            installations.append(item)

        return installations

    async def async_get_site_details(self, installation_id: int) -> dict[str, Any]:
        """Return details for a specific installation."""

        url = f"{API_BASE_URL}/installations/{installation_id}"
        try:
            async with self._session.get(url, headers=self.headers, raise_for_status=True) as response:
                return await response.json()
        except ClientResponseError as err:
            if err.status in (401, 403):
                raise VictronApiAuthError("Invalid API token") from err
            raise VictronApiError(f"Error fetching installation details: {err}") from err
        except ClientError as err:
            raise VictronApiError(f"Error communicating with Victron API: {err}") from err

    async def async_get_latest_values(
        self,
        installation_id: int,
        attribute_ids: list[int],
        device_instance: int,
    ) -> dict[int, float | int | str | None]:
        """Return the most recent datapoint for each attribute id."""

        url = f"{API_BASE_URL}/installations/{installation_id}/widgets/Graph"
        params: list[tuple[str, str]] = [("instance", str(device_instance))]
        params.extend(("attributeIds[]", str(attribute_id)) for attribute_id in attribute_ids)

        try:
            async with self._session.get(url, params=params, headers=self.headers, raise_for_status=True) as response:
                payload = await response.json()
        except ClientResponseError as err:
            if err.status in (401, 403):
                raise VictronApiAuthError("Invalid API token") from err
            raise VictronApiError(f"Error fetching attribute values: {err}") from err
        except ClientError as err:
            raise VictronApiError(f"Error communicating with Victron API: {err}") from err

        records = payload.get("records", {})
        if not isinstance(records, dict):
            raise VictronApiError("Unexpected response structure for attribute values")

        data = records.get("data")
        if not isinstance(data, dict):
            raise VictronApiError("Unexpected data payload from Victron API")

        latest_values: dict[int, float | int | str | None] = {}
        for attribute_id, values in data.items():
            try:
                attribute_key = int(attribute_id)
            except (ValueError, TypeError):
                continue

            latest_value: float | int | str | None = None
            if isinstance(values, list) and values:
                last_entry = values[-1]
                if isinstance(last_entry, list) and len(last_entry) >= 2:
                    latest_value = last_entry[1]
            latest_values[attribute_key] = latest_value

        return latest_values
