import asyncio
import json

import websockets

from .connections import Connections

CONNECTIONS = Connections()


async def request_uname(ws) -> str:
    """Requests a newly connected client's username."""
    await ws.send('{"event": "uname_request"}')
    uname = json.loads(await ws.recv())["uname"]
    if uname in CONNECTIONS.data.keys():
        await ws.send('{"error": "username already used"}')
        await request_uname(ws)
    CONNECTIONS.add_user(uname, ws)
    return uname


async def request_user_limit(ws) -> None:
    """Requests the user limit for the game from the first user who connects."""
    await ws.send('{"event": "ulimit_request"}')
    ulimit = json.loads(await ws.recv())["ulimit"]
    if ulimit < 2 or ulimit % 1 != 0:
        await ws.send('{"error": "ulimit must be an integer greater than 1"}')
        await request_user_limit(ws)
    CONNECTIONS.user_limit = ulimit


async def connect(ws) -> None:
    """
    Websocket connection handler.

    Prompts for a username after checking
    if more users can join, then waits to remove the user when they user_leave
    """
    try:
        if len(CONNECTIONS) >= CONNECTIONS.user_limit:
            await ws.send('{"error": "user limit has been reached"}')
            await ws.close()
            return
    # user_limit has not been assigned a value yet
    except TypeError:
        pass
    uname = await request_uname(ws)
    # This property is initialized to None, so this reliably checks if it has to be requested
    if CONNECTIONS.user_limit is None:
        await request_user_limit(ws)
    try:
        await ws.wait_closed()
    finally:
        CONNECTIONS.remove_user(uname)


async def send_user_count_event() -> None:
    """Sends user count events to all websockets."""
    while True:
        user_count = CONNECTIONS.user_count
        if user_count != len(CONNECTIONS):
            # There should be an extra user if one has joined, and a missing
            # one if one has left
            current_users = CONNECTIONS.current_users
            event_type = "user_join" if user_count < len(CONNECTIONS) else "user_leave"
            user_count = len(CONNECTIONS)
            websockets.broadcast(
                CONNECTIONS.data.values(),
                f'{{"event": "{event_type}", "count": {user_count}, "uname_list": {current_users}}}',
            )
            CONNECTIONS.update_user_count()
        await asyncio.sleep(1)


async def main():
    """Runs the websockets server."""
    async with websockets.serve(connect, "localhost", 8081):
        await send_user_count_event()


if __name__ == "__main__":
    asyncio.run(main())
