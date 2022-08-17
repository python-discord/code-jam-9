from enum import IntEnum


class StatusCode(IntEnum):
    """Custom status codes for a WebSocket event."""

    SUCCESS = 4000
    ROOM_NOT_FOUND = 4001
    INVALID_REQUEST_DATA = 4002
    DATA_NOT_FOUND = 4003
    ROOM_ALREADY_EXISTS = 4004
