import logging

from .camera import KunaCamera
from .errors import AuthenticationError, UnauthorizedError

API_URL = "https://server.kunasystems.com/api/v1"
AUTH_ENDPOINT = "account/auth"
CAMERAS_ENDPOINT = "user/cameras"
RECORDINGS_ENDPOINT = "recordings"

USER_AGENT = "Kuna/2.4.4 (iPhone; iOS 12.1; Scale/3.00)"
USER_AGENT_THUMBNAIL = "Kuna/156 CFNetwork/975.0.3 Darwin/18.2.0"

KUNA_STREAM_URL = "wss://server.kunasystems.com/ws/rtsp/proxy"

_LOGGER = logging.getLogger(__name__)


class KunaAPI:
    """Class for interacting with the Kuna API."""

    def __init__(self, username, password, websession):
        """Initialize the API object."""
        self._username = username
        self._password = password
        self._websession = websession
        self._token = None
        self.cameras = {}

    async def authenticate(self):
        """Login and get an auth token."""
        json = {"email": self._username, "password": self._password}

        result = await self._request("post", AUTH_ENDPOINT, json=json)

        try:
            self._token = result["token"]
        except TypeError:
            raise AuthenticationError(
                "No Kuna API token response returned, check username and password."
            )
        except KeyError as err:
            _LOGGER.error("Error retrieving Kuna auth token: {}".format(err))
            raise err

    async def update(self):
        """Refresh the dict of all cameras in the Kuna account."""
        result = await self._request("get", CAMERAS_ENDPOINT)

        if result is not None:
            new_cameras = {}

            for item in result["results"]:
                new_cameras[item["serial_number"]] = KunaCamera(item, self._request)

            self.cameras = new_cameras

    async def _request(
        self, method, path, params=None, json=None, image=False, allow_redirects=True
    ):
        """Make an async API request."""
        from aiohttp import ClientResponseError

        url = "{}/{}/".format(API_URL, path)
        headers = {"User-Agent": USER_AGENT, "Content-Type": "application/json"}

        if self._token:
            headers["Authorization"] = "Token {}".format(self._token)

        if image or not allow_redirects:
            headers["User-Agent"] = USER_AGENT_THUMBNAIL

        try:
            async with self._websession.request(
                method,
                url,
                params=params,
                json=json,
                headers=headers,
                allow_redirects=allow_redirects,
            ) as result:

                result.raise_for_status()
                if image:
                    return await result.read()
                elif not allow_redirects:
                    return result
                else:
                    return await result.json()

        except ClientResponseError as err:
            if result.status == 403:
                raise UnauthorizedError("Kuna token empty or expired")
            else:
                _LOGGER.error("Kuna API request error: {}".format(err))
