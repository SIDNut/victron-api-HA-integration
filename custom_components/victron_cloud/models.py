"""Data models used by the Victron Cloud integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, TypeAlias

from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import StateType

if TYPE_CHECKING:
    from .coordinator import VictronDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class VictronSensorEntityDescription(SensorEntityDescription):
    """Describe a Victron Cloud sensor entity."""

    attribute_id: int | None = None
    requires: tuple[int, ...] = ()
    value_fn: Callable[[dict[int, StateType]], StateType] | None = None
    available_fn: Callable[[dict[int, StateType]], bool] | None = None


@dataclass(frozen=True)
class VictronRuntimeData:
    """Runtime data stored on the config entry."""

    coordinator: "VictronDataUpdateCoordinator"
    descriptions: tuple[VictronSensorEntityDescription, ...]


VictronConfigEntry: TypeAlias = ConfigEntry[VictronRuntimeData]

