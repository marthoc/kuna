# Kuna Custom Component for Home Assistant

[Home Assistant](https://home-assistant.io/) custom component supporting [Kuna](www.getkuna.com) cameras.

**Home Assistant 0.86 or higher is required**.

For each camera in a Kuna account, the following devices will be created:

- Binary Sensor with device class 'motion', and default name "[Camera Name] Motion".
- Camera with default name "[Camera Name] Camera".
- Switch with default name "[Camera Name] Switch", which controls the camera's light bulb.

**IoT Class:** _Cloud Polling_

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

To enable the component, add the following minimum configuration to `configuration.yaml`:

```yaml
kuna:
  email: YOUR_EMAIL
  password: YOUR_PASSWORD
```

| Config Parameter | Optional/Required | Default | Description |
|------------------|-------------------|---------|-------------|
| email            | Required          | N/A     | The email address used to log into the Kuna app. |
| password         | Required          | N/A     | The password used to log into the Kuna app. |
| recording_interval | Optional        | 7200    | The frequency, in seconds, that the component checks for new recordings for each camera. |
| stream_interval  | Optional          | 5       | The frequency, in seconds, that the camera's frontend streaming view will refresh its image. |
| update_interval  | Optional          | 15      | The frequency, in seconds, that the component polls the Kuna server for updates. |

## Updating

To update the custom component, cd into the `custom_components/kuna` directory and `git pull`.

## Downloading Recordings

On Home Assistant start, and every `recording_interval` seconds thereafter, this component checks the Kuna API for new recordings for each camera in the Kuna account, and fires a Home Assistant event for each recording found. These events can be used in an automation to trigger a download of the video with the `downloader` Home Assistant component. The default `recording_interval`, 7200 seconds (2 hours) corresponds to the length of time that recordings remain in the Kuna system _without_ a premium subscription.

To automatically download new recordings, you must first set up the `downloader` Home Assistant component and then set up an automation.

### Configuring the Downloader Component

Add the following to your configuration.yaml:

```yaml
downloader:
  download_dir: downloads
```
You must ensure that the directory exists before restarting Home Assistant. Given the above example, you would need to ensure that there is a "downloads" subdirectory in your Home Assistant configuration directory, and that the Home Assistant user has write permission to that directory.

Refer to this page for further information on the `downloader` component: https://www.home-assistant.io/components/downloader/

### Automatically Downloading Recordings via Automation

For each recording available in the Kuna API, this component fires a Home Assistant event with the following parameters:

- **event_type**: "kuna_event"   
- **event_data**:
  - **category**: "recording"
  - **serial_number**: the serial number of the camera that generated the recording
  - **label**: a Kuna-assigned string that represents the timestamp of the recording in local time (e.g. "2019_03_18__16_20_06-0400")
  - **timestamp**: a Kuna-assigned string that represents the timestamp of the recording in UTC (e.g. "2019-03-18T20:20:06.986645Z")
  - **duration**: the length of the recording in seconds
  - **url**: the web address at which an mp4 file of the recording is available for download


You can use these parameters to build an automation using the event trigger and templates. To download all recordings, set up the following automation:

```yaml
- alias: Download Kuna recordings
  trigger:
    platform: event
    event_type: kuna_event
    event_data:
      category: recording
  action:
    service: downloader.download_file
    data_template:
      url: '{{ trigger.event.data.url }}'
```

If you want to limit downloads to only a specific camera, add the `serial_number` parameter under 'event_data' in the trigger.


## Caveats

This component has only been tested with a Maximus Smart Light. Testing and feedback by users with other (and multiple!) Kuna devices would be much appreciated!

This custom component retrieves data from the same private API used by the Kuna mobile app, as Kuna does not offer a public API. Be gentle to the API and use at your own risk!

## TODO

- Support streaming from Kuna's websockets streaming endpoint in Home Assistant frontend.
- Support new streams component 