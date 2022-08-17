from typing import TypeAlias

from server.client import Client
from server.errors import RoomAlreadyExistsError, RoomNotFoundError
from server.events import EventResponse
from server.room import Room

ActiveRooms: TypeAlias = dict[str, Room]


class ConnectionManager:
    """Manager for the WebSocket clients."""

    def __init__(self) -> None:
        """Initializes the active connections.

        It stores the active connections and is able to broadcast data.
        """
        self._rooms: ActiveRooms = {}

    def disconnect(self, client: Client, room_code: str) -> None:
        """Removes the connection from the active connections.

        If, after the disconnection, the room is empty, delete it.

        Args:
            client: The client to disconnect.
            room_code: The room from which the client will be disconnected.
        """
        self._rooms[room_code].clients.remove(client)

        if not self._rooms[room_code].clients:
            del self._rooms[room_code]

    def create_room(self, client: Client, room_code: str, difficulty: int) -> None:
        """Create the room for the client.

        Args:
            client: The client that will join to the new room.
            room_code: The room to which the client will be connected.
            difficulty: The difficuty of the room.
        """
        if not self._room_exists(room_code):
            self._rooms[room_code] = Room(client.id, {client}, difficulty)
        else:
            raise RoomAlreadyExistsError(f"The room with code '{room_code}' already exists.")

    def join_room(self, client: Client, room_code: str) -> None:
        """Adds a client to an active room.

        Args:
            client: The client that will join the given room.
            room_code: The room to which the client will be connected.
        """
        if self._room_exists(room_code):
            self._rooms[room_code].clients.add(client)
        else:
            raise RoomNotFoundError(f"The room with code '{room_code}' was not found.")

    async def broadcast(self, data: EventResponse, room_code: str, sender: Client | None = None) -> None:
        """Broadcasts data to all active connections.

        Args:
            data: The data to be sent to the clients.
            room_code: The room to which the data will be sent.
            sender (optional): The client who sent the request.
        """
        for connection in self._rooms[room_code].clients:
            if connection == sender:
                continue
            await connection.send(data)

    def _room_exists(self, room_code: str) -> bool:
        """Checks if a room exists.

        Args:
            room_code: The code associated with a particular room.

        Returns:
            True if the room exists. False otherwise.
        """
        return room_code in self._rooms
