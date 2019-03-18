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
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

REQUIREMENTS = ["pykuna==0.5.0"]

_LOGGER = logging.getLogger(__name__)

DOMAIN = "kuna"

CONF_STREAM_INTERVAL = "stream_interval"
CONF_UPDATE_INTERVAL = "update_interval"

DEFAULT_STREAM_INTERVAL = 5
DEFAULT_UPDATE_INTERVAL = 15

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_EMAIL): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): cv.time_period_seconds,
                vol.Optional(
                    CONF_STREAM_INTERVAL, default=DEFAULT_STREAM_INTERVAL
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
    from pykuna import AuthenticationError, UnauthorizedError

    email = config[DOMAIN][CONF_EMAIL]
    password = config[DOMAIN][CONF_PASSWORD]
    stream_interval = config[DOMAIN][CONF_STREAM_INTERVAL]
    update_interval = config[DOMAIN][CONF_UPDATE_INTERVAL]

    kuna = KunaAccount(email, password, async_get_clientsession(hass), stream_interval)

    try:
        await kuna.account.authenticate()
    except AuthenticationError as err:
        _LOGGER.error("There was an error logging into Kuna: {}".format(err))
        return

    try:
        await kuna.account.update()
    except UnauthorizedError as err:
        _LOGGER.error("There was an error retrieving cameras from Kuna: {}".format(err))
        return

    if not kuna.account.cameras:
        _LOGGER.error("No devices in the Kuna account; aborting component setup.")
        return

    hass.data[DOMAIN] = kuna

    for component in KUNA_COMPONENTS:
        hass.async_create_task(discovery.async_load_platform(hass, component, DOMAIN, {}, config))

    async_track_time_interval(hass, kuna.update, update_interval)

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
    def __init__(self, email, password, websession, stream_interval):
        from pykuna import KunaAPI

        self.account = KunaAPI(email, password, websession)
        self.stream_interval = stream_interval
        self._update_listeners = []

    async def update(self, *_):
        from pykuna import UnauthorizedError

        try:
            _LOGGER.debug("Updating Kuna.")
            await self.account.update()
            for listener in self._update_listeners:
                listener()
        except UnauthorizedError:
            _LOGGER.error("Kuna API authorization error. Refreshing token...")
            await self.account.authenticate()

    def add_update_listener(self, listener):
        self._update_listeners.append(listener)
