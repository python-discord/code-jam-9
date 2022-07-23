import asyncio
import json

import websockets


class Server:
    def __init__(self):
        self.clients = {}
        self.ball_position = (0, 0)
        self.client_positions = {}

    async def main(self):
        async with websockets.serve(self.handler, 'localhost', 8765):
            await asyncio.Future()  # run forever

    async def handler(self, websocket):
        self.clients[str(websocket.id)] = websocket
        async for message in websocket:
            event = json.loads(message)
            print(websocket.id, event)
            if event['type'] == 'paddle':
                # paddle position update
                self.client_positions[str(websocket.id)] = event['data']
                # broadcast all paddle positions to all clients
                broadcast_info = {
                    'type': 'broadcast',
                    'data': {
                        'paddles': self.client_positions,
                        'ball': self.ball_position,
                    }
                }
                websockets.broadcast(self.clients.values(), json.dumps(broadcast_info))
        del self.clients[str(websocket.id)]


if __name__ == '__main__':
    server = Server()
    asyncio.run(server.main())
