class KunaError(Exception):
    pass


class AuthenticationError(KunaError):
    """Raised when authentication fails."""

    pass


class UnauthorizedError(KunaError):
    """Raised when an API call fails as unauthorized (401)."""

    pass
