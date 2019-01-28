"""
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.kuna/
"""
import logging
from datetime import timedelta

from homeassistant.components.camera import Camera
from homeassistant.util.dt import utcnow
from . import DOMAIN

DEPENDENCIES = ['kuna']

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):

    kuna = hass.data[DOMAIN]

    devices = []

    for camera in kuna.account.cameras:
        device = KunaCamera(kuna, camera)
        devices.append(device)

    add_entities(devices, True)


class KunaCamera(Camera):

    def __init__(self, kuna, camera):
        super().__init__()
        self._account = kuna
        self._camera = camera
        self._original_id = self._camera.serial_number
        self._name = '{} Camera'.format(self._camera.name)
        self._unique_id = '{}-Camera'.format(self._camera.serial_number)
        self._last_image = None
        self._time_between_snapshots = timedelta(seconds=30)
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
        return 'Kuna'

    @property
    def is_recording(self):
        """Return the state of the camera."""
        return self.is_streaming

    def update(self):
        """Read new state data from the updated account camera list."""
        kuna = self._account
        self.is_streaming = True
        for camera in kuna.account.cameras:
            if camera.serial_number == self._original_id:
                self._camera = camera

    def update_callback(self):
        """Schedule a state update."""
        self.schedule_update_ha_state(True)

    async def async_added_to_hass(self):
        """Add callback after being added to hass."""
        self._account.add_update_listener(self.update_callback)

    def _ready_for_snapshot(self, now):
        return self._next_snapshot_at is None or now > self._next_snapshot_at

    def camera_image(self):
        """Get and return an image from the camera, only once every 30s."""
        now = utcnow()
        if self._ready_for_snapshot(now):
            self._last_image = self._camera.get_thumbnail()
            self._next_snapshot_at = now + self._time_between_snapshots
        return self._last_image
