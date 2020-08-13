"""
For more details about this platform, please refer to the documentation at
https://github.com/marthoc/kuna
"""
import logging

from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN, MANUFACTURER


_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Kuna only uses config flow for configuration."""
    pass


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Kuna switches from a config entry."""

    kuna = hass.data[DOMAIN]

    devices = []

    for camera in kuna.account.cameras.values():
        device = KunaSwitch(kuna, camera)
        devices.append(device)
        _LOGGER.info("Added switch for Kuna camera: {}".format(device.name))

    async_add_entities(devices, True)


class KunaSwitch(SwitchEntity):
    def __init__(self, kuna, camera):
        self._account = kuna
        self._camera = camera
        self._original_id = self._camera.serial_number
        self._name = "{} Switch".format(self._camera.name)
        self._unique_id = "{}-Switch".format(self._camera.serial_number)

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

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._camera.serial_number)},
            "name": self._camera.name,
            "manufacturer": MANUFACTURER,
            "model": "Camera",
            "sw_version": self._camera.build,
        }

    def update(self):
        """Fetch state data from the updated account camera dict."""
        try:
            self._camera = self._account.account.cameras[self._original_id]
        except KeyError:
            _LOGGER.error(
                "Update failed for {}: camera no longer in Kuna account?".format(
                    self._original_id
                )
            )

    def update_callback(self):
        """Schedule a state update."""
        self.schedule_update_ha_state(True)

    async def async_added_to_hass(self):
        """Add callback after being added to hass."""
        self._account.add_update_listener(self.update_callback)

    async def turn_on(self, **kwargs):
        """Turn the switch on."""
        await self._camera.light_on()
        await self._account.update()

    async def turn_off(self, **kwargs):
        """Turn the device off."""
        await self._camera.light_off()
        await self._account.update()
