"""Sensor platform for the Victron Cloud integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ELECTRIC_CURRENT_AMPERE, ELECTRIC_POTENTIAL_VOLT, ENERGY_KILO_WATT_HOUR, POWER_WATT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DEVICE_INSTANCE,
    CONF_INSTALLATION_ID,
    CONF_INSTALLATION_NAME,
    DOMAIN,
)

if False:  # pragma: no cover - satisfy typing for circular import
    from .coordinator import VictronDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class VictronSensorEntityDescription(SensorEntityDescription):
    """Describes a Victron sensor entity."""

    attribute_id: int | None = None
    requires: tuple[int, ...] = ()
    value_fn: Callable[[dict[int, StateType]], StateType] | None = None
    available_fn: Callable[[dict[int, StateType]], bool] | None = None


BATTERY_STATE_MAP: dict[int, str] = {
    0: "Off",
    2: "Fault",
    3: "Bulk",
    4: "Absorption",
    5: "Float",
    6: "Storage",
    7: "Equalize",
    245: "Off",
    247: "Equalize",
    252: "Ext. Control",
}

LOAD_STATE_MAP: dict[int, str] = {
    0: "Off",
    1: "On",
    2: "Fault",
}


def _calculate_ratio(numerator: int, denominator: int, data: dict[int, StateType]) -> StateType:
    num = data.get(numerator)
    den = data.get(denominator)
    if num is None or den in (None, 0):
        return None
    try:
        return float(num) / float(den)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _calculate_product(factor_a: int, factor_b: int, data: dict[int, StateType]) -> StateType:
    a = data.get(factor_a)
    b = data.get(factor_b)
    if a is None or b is None:
        return None
    try:
        return float(a) * float(b)
    except (TypeError, ValueError):
        return None


def _map_state(mapping: dict[int, str], attribute_id: int, data: dict[int, StateType]) -> StateType:
    raw = data.get(attribute_id)
    if raw is None:
        return None
    try:
        return mapping.get(int(raw), "Unknown")
    except (TypeError, ValueError):
        return "Unknown"


SENSOR_DESCRIPTIONS: tuple[VictronSensorEntityDescription, ...] = (
    VictronSensorEntityDescription(
        key="solar_power",
        translation_key="solar_power",
        name="Victron Solar Power",
        attribute_id=442,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=POWER_WATT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
    ),
    VictronSensorEntityDescription(
        key="solar_voltage",
        translation_key="solar_voltage",
        name="Victron Solar Voltage",
        attribute_id=86,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=ELECTRIC_POTENTIAL_VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
    ),
    VictronSensorEntityDescription(
        key="solar_current",
        translation_key="solar_current",
        name="Victron Solar Current",
        requires=(442, 86),
        native_unit_of_measurement=ELECTRIC_CURRENT_AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CURRENT,
        icon="mdi:current-dc",
        value_fn=lambda data: _calculate_ratio(442, 86, data),
    ),
    VictronSensorEntityDescription(
        key="battery_current",
        translation_key="battery_current",
        name="Victron Battery Current",
        attribute_id=82,
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=ELECTRIC_CURRENT_AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
    ),
    VictronSensorEntityDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        name="Victron Battery Voltage",
        attribute_id=81,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=ELECTRIC_POTENTIAL_VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:car-battery",
    ),
    VictronSensorEntityDescription(
        key="battery_state",
        translation_key="battery_state",
        name="Victron Battery State",
        attribute_id=85,
        icon="mdi:battery-heart",
        value_fn=lambda data: _map_state(BATTERY_STATE_MAP, 85, data),
    ),
    VictronSensorEntityDescription(
        key="battery_power",
        translation_key="battery_power",
        name="Victron Battery Power",
        requires=(81, 82),
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=POWER_WATT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-positive",
        value_fn=lambda data: _calculate_product(81, 82, data),
    ),
    VictronSensorEntityDescription(
        key="load_current",
        translation_key="load_current",
        name="Victron Load Current",
        attribute_id=242,
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=ELECTRIC_CURRENT_AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
    ),
    VictronSensorEntityDescription(
        key="load_state",
        translation_key="load_state",
        name="Victron Load State",
        attribute_id=241,
        icon="mdi:toggle-switch",
        value_fn=lambda data: _map_state(LOAD_STATE_MAP, 241, data),
    ),
    VictronSensorEntityDescription(
        key="load_power",
        translation_key="load_power",
        name="Victron Load Power",
        requires=(81, 242),
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=POWER_WATT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
        value_fn=lambda data: _calculate_product(81, 242, data),
    ),
    VictronSensorEntityDescription(
        key="solar_energy_today",
        translation_key="solar_energy_today",
        name="Victron Solar Energy Today",
        attribute_id=94,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:solar-power",
    ),
)

SENSOR_MAP: dict[str, VictronSensorEntityDescription] = {
    description.key: description for description in SENSOR_DESCRIPTIONS
}

DEFAULT_SENSOR_KEYS: list[str] = [description.key for description in SENSOR_DESCRIPTIONS]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Victron Cloud sensors."""

    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: "VictronDataUpdateCoordinator" = data["coordinator"]
    descriptions: Iterable[VictronSensorEntityDescription] = data["descriptions"]

    entities: list[VictronSensor] = [
        VictronSensor(coordinator, entry, description) for description in descriptions
    ]

    async_add_entities(entities)


class VictronSensor(CoordinatorEntity["VictronDataUpdateCoordinator"], SensorEntity):
    """Representation of a Victron sensor."""

    entity_description: VictronSensorEntityDescription

    def __init__(
        self,
        coordinator: "VictronDataUpdateCoordinator",
        entry: ConfigEntry,
        description: VictronSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}-{description.key}"
        self._attr_has_entity_name = True
        installation_name = entry.data.get(CONF_INSTALLATION_NAME)
        installation_id = entry.data.get(CONF_INSTALLATION_ID)
        device_instance = entry.data.get(CONF_DEVICE_INSTANCE)
        model = f"Instance {device_instance}" if device_instance is not None else "VRM"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(installation_id))},
            name=installation_name or "Victron Installation",
            manufacturer="Victron Energy",
            model=model,
        )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""

        data = self.coordinator.data
        description = self.entity_description

        if description.value_fn is not None:
            return description.value_fn(data)

        if description.attribute_id is None:
            return None

        return data.get(description.attribute_id)

    @property
    def available(self) -> bool:
        """Return True if the entity is available."""

        data = self.coordinator.data
        description = self.entity_description

        if description.available_fn is not None:
            return description.available_fn(data)

        if description.attribute_id is not None:
            return description.attribute_id in data and data[description.attribute_id] is not None

        return super().available

    @property
    def extra_state_attributes(self) -> dict[str, StateType]:
        """Return extra attributes with raw values."""

        description = self.entity_description
        attributes: dict[str, StateType] = {}

        if description.attribute_id is not None:
            attributes["attribute_id"] = description.attribute_id
            attributes["raw_value"] = self.coordinator.data.get(description.attribute_id)

        return attributes
