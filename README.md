# Kuna Custom Component for Home Assistant

This is a custom [Home Assistant](https://home-assistant.io/) component to support [Kuna](www.getkuna.com) cameras.

**Home Assistant 0.86 or higher is required**.

Eventually this custom component will be PR'd and (hopefully) merged into Home Assistant. I'm publishing it as a custom component now for testing and feedback.

For each camera in a Kuna account, the following devices will be created:

- Binary Sensor with device class 'motion', and default name "[Camera Name] Motion".
- Camera (supporting still images (rate-limited at 30s), streaming support will be added soon), with default name "[Camera Name] Camera".
- Switch with default name "[Camera Name] Switch", which controls the camera's light bulb.

Note:

- The private Kuna API only supports polling (and this component polls every 15 seconds). There may therefore be a lag between when motion is detected or the light is turned on manually and the change is reflected in the Home Assistant UI.
- Entities may be renamed from the Home Assistant UI.
- State attributes will be added to entities eventually.

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

Add the following to `configuration.yaml`:

```
kuna:
  email: YOUR_EMAIL
  password: YOUR_PASSWORD
```

Where YOUR_EMAIL and YOUR_PASSWORD are the credentials you use to log into the Kuna mobile app.

## Updating

To update the custom component, cd into the `custom_components/kuna` directory and `git pull`.

## Caveats

This component has only been tested with a Maximus Smart Light. Testing and feedback by users with other (and multiple!) Kuna devices would be much appreciated!

This custom component retrieves data from the same private API used by the Kuna mobile app, as Kuna does not offer a public API. It tries to be gentle to the API by polling for changes for the whole account only once every 15 seconds. Use at your own risk!
