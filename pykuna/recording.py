"""Models a recording from the Kuna API."""
from .kuna import API_URL


class KunaRecording:
    """Represents a Kuna recording."""

    def __init__(self, raw, request):
        self._raw = raw
        self._request = request

    @property
    def url(self):
        return self._raw["url"]

    @property
    def id(self):
        return self._raw["id"]

    @property
    def label(self):
        return self._raw["label"]

    @property
    def camera(self):
        return self._raw["camera"]

    @property
    def description(self):
        return self._raw["description"]

    @property
    def timestamp(self):
        return self._raw["timestamp"]

    @property
    def duration(self):
        return self._raw["duration"]

    @property
    def status(self):
        return self._raw["status"]

    @property
    def m3u8(self):
        return self._raw["m3u8"]

    @property
    def thumbnails(self):
        return self._raw["thumbnails"]

    @property
    def classification(self):
        return self._raw["classification"]

    @property
    def created_at(self):
        return self._raw["created_at"]

    @property
    def updated_at(self):
        return self._raw["updated_at"]

    @property
    def mp4(self):
        return self._raw["mp4"]

    async def get_download_link(self):
        """Query the mp4 endpoint and return the redirect link for consumption."""
        result = await self._request(
            "get", self.mp4.replace(API_URL, ""), allow_redirects=False
        )
        return result.headers["Location"]
