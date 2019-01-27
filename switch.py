"""
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.kuna/
"""
import logging

from homeassistant.components.switch import SwitchDevice
from . import DOMAIN

DEPENDENCIES = ['kuna']

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):

    kuna = hass.data[DOMAIN]

    devices = []

    for camera in kuna.account.cameras:
        device = KunaSwitch(kuna, camera)
        devices.append(device)

    add_entities(devices)


class KunaSwitch(SwitchDevice):

    def __init__(self, kuna, camera):
        self._account = kuna
        self._camera = camera
        self._original_id = self._camera.serial_number
        self._name = '{} Switch'.format(self._camera.name)
        self._unique_id = '{}-Switch'.format(self._camera.serial_number)

    @property
    def available(self):
        return self._camera.status

    @property
    def should_poll(self):
        return False

    @property
    def unique_id(self):
        """Return the unique ID of the switch."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the switch."""
        return self._camera.bulb_on

    def update(self):
        """Read new state data from the updated account camera list."""
        kuna = self._account
        for camera in kuna.account.cameras:
            if camera.serial_number == self._original_id:
                self._camera = camera

    def update_callback(self):
        """Schedule a state update."""
        self.schedule_update_ha_state(True)

    async def async_added_to_hass(self):
        """Add callback after being added to hass."""
        self._account.add_update_listener(self.update_callback)

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self._camera.light_on()
        self._account.update()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        self._camera.light_off()
        self._account.update()
