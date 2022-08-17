"""The main WebSocket server.

This server handles user connection, disconnection and events.
"""
from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from server.client import Client
from server.connection_manager import ConnectionManager
from server.event_handler import EventHandler

app = FastAPI()


manager = ConnectionManager()


@app.websocket("/room")
async def room(websocket: WebSocket) -> None:
    """This is the endpoint for the WebSocket connection.

    It creates a client and handles connection and disconnection with the
    ConnectionManager. It continuously receives and broadcasts data to the
    active clients.
    """
    client = Client(websocket)
    await client.accept()

    handler = EventHandler(client, manager)

    initial_event = await client.receive()
    await handler.handle_initial_connection(initial_event)

    try:
        while True:
            event = await client.receive()
            closed = await handler(event)
            if closed:
                break
    except WebSocketDisconnect:
        return
