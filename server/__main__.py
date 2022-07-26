import asyncio
import json

import websockets

CONNECTIONS = {}
USER_COUNT = len(CONNECTIONS)
USER_LIMIT = int()
LAST_USER = str()


async def request_uname(ws):
    """Requests a newly connected client's username."""
    global USER_LIMIT
    await ws.send('{"event": "uname_request"}')
    uname = json.loads(await ws.recv())["uname"]
    if uname in list(CONNECTIONS.keys()):
        await ws.send('{"error": "username already used"}')
        await request_uname(ws)
    CONNECTIONS[uname] = ws
    return uname


async def request_user_limit(ws):
    """Requests the user limit for the game from the first user who connects."""
    global USER_LIMIT
    await ws.send('{"event": "ulimit_request"}')
    ulimit = json.loads(await ws.recv())["ulimit"]
    if ulimit < 2:
        await ws.send('{"error": "ulimit must be larger than 1"}')
        await request_user_limit(ws)
    USER_LIMIT = ulimit


async def connect(ws):
    """Websocket handler function to handle connections."""
    global LAST_USER
    uname = await request_uname(ws)
    if len(CONNECTIONS) == 1:
        await request_user_limit(ws)
    try:
        await ws.wait_closed()
    finally:
        LAST_USER = uname
        del CONNECTIONS[uname]


async def send_user_count_event():
    """Sends user count events to all websockets."""
    global CONNECTIONS
    global USER_COUNT
    while True:
        if USER_COUNT < len(CONNECTIONS):
            USER_COUNT = len(CONNECTIONS)
            websockets.broadcast(
                CONNECTIONS.values(),
                f'{{"event": "user_join", "count": {USER_COUNT}, "uname": "{list(CONNECTIONS.keys())[-1]}"}}',
            )
        elif USER_COUNT > len(CONNECTIONS):
            USER_COUNT = len(CONNECTIONS)
            websockets.broadcast(
                CONNECTIONS.values(),
                f'{{"event": "user_leave", "count": {USER_COUNT}, "uname": "{LAST_USER}"}}',
            )
        await asyncio.sleep(1)


async def main():
    """Runs the websockets server."""
    async with websockets.serve(connect, "localhost", 8081):
        await send_user_count_event()


if __name__ == "__main__":
    asyncio.run(main())
