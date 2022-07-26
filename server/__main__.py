import asyncio

import websockets

CONNECTIONS = set()
USER_COUNT = len(CONNECTIONS)


async def connect(ws):
    """Websocket handler function to handle connections."""
    CONNECTIONS.add(ws)
    try:
        await ws.wait_closed()
    finally:
        CONNECTIONS.remove(ws)


async def send_user_count_event():
    """Sends user count events to all websockets."""
    global CONNECTIONS
    global USER_COUNT
    while True:
        if USER_COUNT < len(CONNECTIONS):
            USER_COUNT = len(CONNECTIONS)
            websockets.broadcast(
                CONNECTIONS, f'{{"event": "user_join", "count": {USER_COUNT}}}'
            )
        elif USER_COUNT > len(CONNECTIONS):
            USER_COUNT = len(CONNECTIONS)
            websockets.broadcast(
                CONNECTIONS, f'{{"event": "user_leave", "count": {USER_COUNT}}}'
            )
        await asyncio.sleep(1)


async def main():
    """Runs the websockets server."""
    async with websockets.serve(connect, "localhost", 8081):
        await send_user_count_event()


if __name__ == "__main__":
    asyncio.run(main())
