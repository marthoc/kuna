"""
For more details about this platform, please refer to the documentation at
https://github.com/marthoc/kuna
"""
import logging

from homeassistant.components.camera import Camera
from homeassistant.util.dt import utcnow
from . import DOMAIN, ATTR_SERIAL_NUMBER


DEPENDENCIES = ["kuna"]

ATTR_NOTIFICATIONS_ENABLED = "notifications_enabled"
ATTR_VOLUME = "volume"

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):

    kuna = hass.data[DOMAIN]

    devices = []

    for camera in kuna.account.cameras.values():
        device = KunaCamera(kuna, camera)
        devices.append(device)
        _LOGGER.info("Added camera for Kuna camera: {}".format(device.name))

    async_add_entities(devices, True)


class KunaCamera(Camera):
    def __init__(self, kuna, camera):
        super().__init__()
        self._account = kuna
        self._camera = camera
        self._original_id = self._camera.serial_number
        self._name = "{} Camera".format(self._camera.name)
        self._unique_id = "{}-Camera".format(self._camera.serial_number)
        self._last_image = None
        self._next_snapshot_at = None

    @property
    def available(self):
        return self._camera.status

    @property
    def unique_id(self):
        """Return the unique ID of the camera."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the camera."""
        return self._name

    @property
    def brand(self):
        return "Kuna"

    @property
    def is_recording(self):
        """Return the state of the camera."""
        return self._camera.recording_active

    @property
    def device_state_attributes(self):
        attributes = {
            ATTR_SERIAL_NUMBER: self._camera.serial_number,
            ATTR_NOTIFICATIONS_ENABLED: self._camera.notifications_enabled,
            ATTR_VOLUME: self._camera.volume,
        }
        return attributes

    def update(self):
        """Fetch state data from the updated account camera dict."""
        self.is_streaming = True
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

    def _ready_for_snapshot(self, now):
        return self._next_snapshot_at is None or now > self._next_snapshot_at

    async def camera_image(self):
        """Get and return an image from the camera, only once every stream_interval seconds."""
        now = utcnow()
        if self._ready_for_snapshot(now):
            self._last_image = await self._camera.get_thumbnail()
            self._next_snapshot_at = now + self._account.stream_interval
        return self._last_image
