import asyncio
import json

import websockets


class Client:
    def __init__(self):
        self.paddle_position = (0, 0)
        self.websocket = None
        self.other_paddle_positions = {}

    async def main(self):
        self.websocket = await websockets.connect('ws://localhost:8765')
        try:
            while True:
                await self.websocket.send(json.dumps({'type': 'paddle', 'data': self.paddle_position}))
                msg = await self.websocket.recv()
                print(json.loads(msg))
                await asyncio.sleep(1)
        finally:
            await self.websocket.close()


if __name__ == '__main__':
    client = Client()
    asyncio.run(client.main())
