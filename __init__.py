"""
Support for Kuna (www.getkuna.com).

For more details about this component, please refer to the documentation at
https://github.com/marthoc/kuna
"""
import logging

import voluptuous as vol

from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.const import (
    CONF_EMAIL,
    CONF_EVENT,
    CONF_PASSWORD,
    EVENT_HOMEASSISTANT_START,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "kuna"

CONF_RECORDING_INTERVAL = "recording_interval"
CONF_STREAM_INTERVAL = "stream_interval"
CONF_UPDATE_INTERVAL = "update_interval"

DEFAULT_RECORDING_INTERVAL = 7200
DEFAULT_STREAM_INTERVAL = 5
DEFAULT_UPDATE_INTERVAL = 15

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_EMAIL): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(
                    CONF_RECORDING_INTERVAL, default=DEFAULT_RECORDING_INTERVAL
                ): cv.time_period_seconds,
                vol.Optional(
                    CONF_STREAM_INTERVAL, default=DEFAULT_STREAM_INTERVAL
                ): cv.time_period_seconds,
                vol.Optional(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): cv.time_period_seconds,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

KUNA_COMPONENTS = ["binary_sensor", "camera", "switch"]

ATTR_SERIAL_NUMBER = "serial_number"

SERVICE_ENABLE_NOTIFICATIONS = "enable_notifications"
SERVICE_DISABLE_NOTIFICATIONS = "disable_notifications"

SERVICE_NOTIFICATIONS_SCHEMA = vol.Schema({vol.Optional(ATTR_SERIAL_NUMBER): cv.string})


async def async_setup(hass, config):
    """Set up Kuna."""
    email = config[DOMAIN][CONF_EMAIL]
    password = config[DOMAIN][CONF_PASSWORD]
    recording_interval = config[DOMAIN][CONF_RECORDING_INTERVAL]
    stream_interval = config[DOMAIN][CONF_STREAM_INTERVAL]
    update_interval = config[DOMAIN][CONF_UPDATE_INTERVAL]

    kuna = KunaAccount(
        hass,
        email,
        password,
        async_get_clientsession(hass),
        recording_interval,
        stream_interval,
    )

    if not await kuna.authenticate():
        return False

    await kuna.account.update()

    if not kuna.account.cameras:
        _LOGGER.error("No devices in the Kuna account; aborting component setup.")
        return False

    hass.data[DOMAIN] = kuna

    for component in KUNA_COMPONENTS:
        hass.async_create_task(
            discovery.async_load_platform(hass, component, DOMAIN, {}, config)
        )

    async_track_time_interval(hass, kuna.update, update_interval)

    async_track_time_interval(hass, kuna.scan_for_recordings, recording_interval)

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, kuna.scan_for_recordings)

    async def enable_notifications(call):
        serial_number = call.data.get(ATTR_SERIAL_NUMBER)
        kuna = hass.data[DOMAIN]

        if serial_number is None:
            for camera in kuna.account.cameras.values():
                await camera.enable_notifications()
        else:
            try:
                await kuna.account.cameras[serial_number].enable_notifications()
            except KeyError:
                _LOGGER.error(
                    "Kuna service call error: no camera with serial number '{}' in account.".format(
                        serial_number
                    )
                )

    hass.services.async_register(
        DOMAIN,
        SERVICE_ENABLE_NOTIFICATIONS,
        enable_notifications,
        schema=SERVICE_NOTIFICATIONS_SCHEMA,
    )

    async def disable_notifications(call):
        serial_number = call.data.get(ATTR_SERIAL_NUMBER)
        kuna = hass.data[DOMAIN]

        if serial_number is None:
            for camera in kuna.account.cameras.values():
                await camera.disable_notifications()
        else:
            try:
                await kuna.account.cameras[serial_number].disable_notifications()
            except KeyError:
                _LOGGER.error(
                    "Kuna service call error: no camera with serial number '{}' in account.".format(
                        serial_number
                    )
                )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DISABLE_NOTIFICATIONS,
        disable_notifications,
        schema=SERVICE_NOTIFICATIONS_SCHEMA,
    )

    return True


class KunaAccount:
    """Represents a Kuna account."""

    def __init__(
        self, hass, email, password, websession, recording_interval, stream_interval
    ):
        from .pykuna import KunaAPI

        self._hass = hass
        self.account = KunaAPI(email, password, websession)
        self._recording_interval = recording_interval
        self.stream_interval = stream_interval
        self._update_listeners = []

    async def update(self, *_):
        from .pykuna import UnauthorizedError

        try:
            _LOGGER.debug("Updating Kuna.")
            await self.account.update()
            for listener in self._update_listeners:
                listener()
        except UnauthorizedError:
            _LOGGER.error("Kuna API authorization error. Refreshing token...")
            await self.authenticate()

    async def authenticate(self) -> bool:
        from async_timeout import timeout
        from asyncio import TimeoutError

        async with timeout(30):
            try:
                await self.account.authenticate()
                return True
            except TimeoutError:
                _LOGGER.error("Timeout while authenticating Kuna.")
                return False
            except Exception as err:
                _LOGGER.error("Error while authenticating Kuna: {}".format(err))
                raise err
                return False

    def add_update_listener(self, listener):
        self._update_listeners.append(listener)

    async def scan_for_recordings(self, *_):
        """
        Queries the Kuna API for recordings for each camera in the account.
        Fires an event with the recording data for consumption by other services.
        """
        _LOGGER.debug("Scanning for Kuna recordings.")
        recordings = []
        for camera in self.account.cameras.values():
            recs = await camera.get_recordings_by_time(self._recording_interval)
            for item in recs:
                recordings.append(item)

        for recording in recordings:
            url = await recording.get_download_link()

            if url is not None:
                event_data = {
                    "category": "recording",
                    "camera_name": self.account.cameras[recording.camera["serial_number"]].name,
                    "serial_number": recording.camera["serial_number"],
                    "label": recording.label,
                    "timestamp": recording.timestamp,
                    "duration": recording.duration,
                    "url": url,
                }
                self._hass.bus.async_fire(
                    "{}_{}".format(DOMAIN, CONF_EVENT), event_data
                )
            else:
                _LOGGER.error(
                    "Error retrieving download url for Kuna recording: {} ({})".format(
                        recording.label, recording.camera["serial_number"]
                    )
                )
