import asyncio
import json
import random

import websockets


class Client:
    def __init__(self):
        self.paddle_position = (0, 50)
        self.websocket = None
        self.other_paddle_positions = {}

    async def main(self):
        self.websocket = await websockets.connect('ws://localhost:8765')
        try:
            while True:
                self.rand_position()
                await self.websocket.send(json.dumps({'type': 'paddle', 'data': self.paddle_position}))
                msg = await self.websocket.recv()
                print(json.loads(msg))
                await asyncio.sleep(1)
        finally:
            await self.websocket.close()

    def rand_position(self):
        self.paddle_position = (0, random.randint(0, 400))

if __name__ == '__main__':
    client = Client()
    asyncio.run(client.main())
