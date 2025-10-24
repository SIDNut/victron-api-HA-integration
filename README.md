# Victron Cloud Home Assistant integration

This repository contains a Home Assistant custom integration that connects to the Victron VRM cloud API. It replaces the manual REST sensors with a guided configuration flow, automatic entity creation, and secure token storage. The integration can be installed through [HACS](https://hacs.xyz/) and exposes the most common Victron metrics as Home Assistant sensors.

## Features

- Step-by-step setup flow that walks you through creating a VRM API token and selecting your installation
- Secure storage of the API token in Home Assistant's config entry storage
- Configurable polling interval and selectable sensors
- Derived sensors for solar/battery currents and power
- Device metadata populated from your Victron installation

## Prerequisites

1. A Victron VRM account with access to the installation you want to monitor
2. An API token created in the VRM portal under **My account → Integrations** ([direct link](https://vrm.victronenergy.com/profile/integrations))
3. The GX device instance number for the installation (available from the Device List in the VRM portal)

## Installation (HACS)

1. Open HACS in Home Assistant and add this repository as a custom integration repository.
2. Search for **Victron Cloud** and install the integration.
3. Restart Home Assistant when prompted.

Alternatively you can copy the `custom_components/victron_cloud` directory into your Home Assistant `config/custom_components` folder manually. Restart Home Assistant afterwards.

## Initial setup

1. In Home Assistant go to **Settings → Devices & Services → Add Integration** and search for **Victron Cloud**.
2. Enter your VRM API token when prompted. The integration validates the token and retrieves the installations you can access.
3. Select the installation you want to monitor and provide the GX device instance number shown in the VRM Device List.
4. Finish the flow to create the config entry. Home Assistant stores the token securely in `.storage` and creates the default set of sensors.

### Available sensors

By default the integration creates the following entities (you can enable/disable them later in the options flow):

| Entity | Description | Source attribute |
| ------ | ----------- | ---------------- |
| `sensor.victron_solar_power` | PV array power in watts | Attribute 442 |
| `sensor.victron_solar_voltage` | PV array voltage in volts | Attribute 86 |
| `sensor.victron_solar_current` | Derived PV array current | 442 / 86 |
| `sensor.victron_battery_current` | Battery current in amperes | Attribute 82 |
| `sensor.victron_battery_voltage` | Battery voltage in volts | Attribute 81 |
| `sensor.victron_battery_state` | Battery charge mode | Attribute 85 |
| `sensor.victron_battery_power` | Derived battery power | 81 × 82 |
| `sensor.victron_load_current` | DC load current | Attribute 242 |
| `sensor.victron_load_state` | DC load state | Attribute 241 |
| `sensor.victron_load_power` | Derived DC load power | 81 × 242 |
| `sensor.victron_solar_energy_today` | Solar energy produced today (kWh) | Attribute 94 |

You can adjust the list of sensors and the polling interval from the integration options menu.

## Re-authentication

If the VRM API token expires or is revoked you will be prompted to re-authenticate. Provide a new API token in the flow and the integration will update the stored credentials and reload automatically.

## Development

The file `victron_extracted_data_formatted.csv` contains a comprehensive mapping of VRM attribute IDs that was used while building the integration. It can be used as a reference for extending the integration with additional sensors.

## Credits

- Victron Energy for providing the VRM API
- The Home Assistant community for tooling and examples that inspired this integration
