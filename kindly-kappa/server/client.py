from json import JSONDecodeError
from uuid import uuid4

from fastapi import WebSocket
from pydantic import ValidationError

from server.codes import StatusCode
from server.events import ErrorData, EventRequest, EventResponse, EventType, ReplaceData


class Client:
    """A WebSocket client."""

    def __init__(self, websocket: WebSocket) -> None:
        """Initializes the WebSocket and the ID.

        A client is identified by an ID and contains the corresponding WebSocket
        that is used to send and receive messages.
        Args:
            websocket: A WebSocket instance.
        """
        self._websocket = websocket
        self.id = uuid4()
        self.default_replacement = EventRequest(
            type=EventType.REPLACE, data=ReplaceData(code=[{"from": 0, "to": 0, "value": ""}])
        )

        self.username: str

    async def accept(self) -> None:
        """Accepts the WebSocket connection."""
        await self._websocket.accept()

    async def send(self, data: EventResponse) -> None:
        """Sends JSON data over the WebSocket connection.

        Args:
            data: The data to be sent to the client.
        """
        await self._websocket.send_json(data.dict())

    async def receive(self) -> EventRequest:
        """Receives JSON data over the WebSocket connection.

        Returns:
            The data received from the client or default EventRequests if an
            error occured.
        """
        try:
            return EventRequest(**await self._websocket.receive_json())
        except (TypeError, JSONDecodeError):
            await self.send(
                EventResponse(
                    type=EventType.ERROR,
                    data=ErrorData(message="Invalid request data."),
                    status_code=StatusCode.INVALID_REQUEST_DATA,
                ),
            )
            return self.default_replacement
        except (KeyError, ValidationError):
            await self.send(
                EventResponse(
                    type=EventType.ERROR,
                    data=ErrorData(message="Data not found."),
                    status_code=StatusCode.DATA_NOT_FOUND,
                ),
            )
            return self.default_replacement

    async def close(self) -> None:
        """Closes the WebSocket connection."""
        return await self._websocket.close()

    def __eq__(self, other: object) -> bool:
        """Compares the Client to another object.

        If the object is not an instance of Client, NotImplemented is returned.
        Args:
            other: The object to compare the client to.
        Returns:
            True if the id of the client is equal to the other client's id,
            False otherwise.
        """
        if not isinstance(other, Client):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Returns the hash value of the Client."""
        return hash(self.id)
