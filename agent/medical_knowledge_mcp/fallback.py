class OfficialSourceUnavailable(RuntimeError):
    """Raised when every configured official source cannot be queried."""

    def __init__(self, message: str = "official sources unavailable") -> None:
        super().__init__(message)
