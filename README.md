# Kuna Custom Component for Home Assistant

This is a custom [Home Assistant](https://home-assistant.io/) component to support [Kuna](www.getkuna.com) cameras.

**Home Assistant 0.86 or higher is required**.

For each camera in a Kuna account, the following devices will be created:

- Binary Sensor with device class 'motion', and default name "[Camera Name] Motion".
- Camera with default name "[Camera Name] Camera".
- Switch with default name "[Camera Name] Switch", which controls the camera's light bulb.

Note:

- The private Kuna API only supports polling. There may therefore be a lag between when motion is detected or the light is turned on manually and the change is reflected in the Home Assistant UI.
- Entities may be renamed from the Home Assistant UI.

## Installation (Home Assistant >= 0.86)
This custom component must be installed for it to be loaded by Home Assistant.

1. Create a `custom_components` directory in your Home Assistant configuration directory ('config' share if using [hass.io](https://home-assistant.io/hassio/) with the [Samba](https://home-assistant.io/addons/samba/) add-on or `~/.home-assistant/` for Linux installations).
1. Get the latest release from GitHub by cd'ing into the custom_components directory and cloning this repo (example below for Hass.io):
```
cd /config/custom_components
git clone https://github.com/marthoc/kuna
```

Now, proceed with configuration.

## Configuration

Add the following minimum configuration to `configuration.yaml`:

```
kuna:
  email: YOUR_EMAIL
  password: YOUR_PASSWORD
```

| Config Parameter | Optional/Required | Default | Description |
|------------------|-------------------|---------|-------------|
| email            | Required          | N/A     | The email address used to log into the Kuna app. |
| password         | Required          | N/A     | The password used to log into the Kuna app. |
| stream_interval  | Optional          | 5       | The frequency, in seconds, that the camera's frontend streaming view will refresh its image. |
| update_interval  | Optional          | 15      | The frequency, in seconds, that the component polls the Kuna server for updates. |

## Updating

To update the custom component, cd into the `custom_components/kuna` directory and `git pull`.

## Caveats

This component has only been tested with a Maximus Smart Light. Testing and feedback by users with other (and multiple!) Kuna devices would be much appreciated!

This custom component retrieves data from the same private API used by the Kuna mobile app, as Kuna does not offer a public API. Be gentle to the API and use at your own risk!

# TODO

- Add device state attributes to entities.
- Add services to modify device state attributes.
- Support real streaming from Kuna's websockets streaming endpoint in Home Assistant frontend.