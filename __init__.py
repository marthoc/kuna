"""
Support for Kuna (www.getkuna.com).

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/kuna/
"""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.helpers.event import track_time_interval
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

REQUIREMENTS = ['pykuna==0.4.0']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'kuna'

CONF_STREAM_INTERVAL = 'stream_interval'
CONF_UPDATE_INTERVAL = 'update_interval'

DEFAULT_STREAM_INTERVAL = 5
DEFAULT_UPDATE_INTERVAL = 15

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): cv.time_period_seconds,
        vol.Optional(CONF_STREAM_INTERVAL, default=DEFAULT_STREAM_INTERVAL): cv.time_period_seconds
    }),
}, extra=vol.ALLOW_EXTRA)

KUNA_COMPONENTS = ['binary_sensor', 'camera', 'switch']

ATTR_SERIAL_NUMBER = 'serial_number'

def setup(hass, config):
    """Set up Kuna."""
    from pykuna import AuthenticationError, UnauthorizedError

    email = config[DOMAIN][CONF_EMAIL]
    password = config[DOMAIN][CONF_PASSWORD]
    stream_interval = config[DOMAIN][CONF_STREAM_INTERVAL]
    update_interval = config[DOMAIN][CONF_UPDATE_INTERVAL]

    kuna = KunaAccount(email, password, stream_interval)

    try:
        kuna.account.authenticate()
    except AuthenticationError as err:
        _LOGGER.error('There was an error logging into Kuna: {}'.format(err))
        return

    try:
        kuna.account.update()
    except UnauthorizedError as err:
        _LOGGER.error('There was an error retrieving cameras from Kuna: {}'.format(err))
        return

    if not kuna.account.cameras:
        _LOGGER.error('No devices in the Kuna account; aborting component setup.')
        return

    hass.data[DOMAIN] = kuna

    for component in KUNA_COMPONENTS:
        discovery.load_platform(hass, component, DOMAIN, {}, config)

    track_time_interval(hass, kuna.update, update_interval)

    return True


class KunaAccount:
    """Represents a Kuna account."""

    def __init__(self, email, password, stream_interval):
        from pykuna import KunaAPI
        self.account = KunaAPI(email, password)
        self.stream_interval = stream_interval
        self._update_listeners = []

    def update(self, *_):
        from pykuna import UnauthorizedError
        try:
            _LOGGER.debug('Updating Kuna.')
            self.account.update()
            for listener in self._update_listeners:
                listener()
        except UnauthorizedError:
            _LOGGER.error('Kuna API authorization error. Refreshing token...')
            self.account.authenticate()

    def add_update_listener(self, listener):
        self._update_listeners.append(listener)
