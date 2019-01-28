"""
Support for Kuna (www.getkuna.com).

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/kuna/
"""
from datetime import timedelta
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.helpers.event import track_time_interval
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

REQUIREMENTS = ['pykuna==0.3.0']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'kuna'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }),
}, extra=vol.ALLOW_EXTRA)

KUNA_COMPONENTS = ['binary_sensor', 'camera', 'switch']

REFRESH_INTERVAL = 15


def setup(hass, config):
    """Set up Kuna."""
    from pykuna import AuthenticationError, UnauthorizedError

    email = config[DOMAIN][CONF_EMAIL]
    password = config[DOMAIN][CONF_PASSWORD]

    kuna = KunaAccount(email, password)

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

    hass.data[DOMAIN] = kuna

    for component in KUNA_COMPONENTS:
        discovery.load_platform(hass, component, DOMAIN, {}, config)

    track_time_interval(hass, kuna.update, timedelta(seconds=REFRESH_INTERVAL))

    return True


class KunaAccount:
    """Represents a Kuna account."""

    def __init__(self, email, password):
        from pykuna import KunaAPI
        self.account = KunaAPI(email, password)
        self._update_listeners = []

    def update(self, *_):
        from pykuna import UnauthorizedError
        try:
            self.account.update()
            for listener in self._update_listeners:
                listener()
        except UnauthorizedError:
            _LOGGER.error('Kuna API authorization error. Attempting to refresh token...')
            self.account.authenticate()

    def add_update_listener(self, listener):
        self._update_listeners.append(listener)
