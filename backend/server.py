"""The server code."""

import asyncio
import json
import random

from ball import Ball
import websockets


class Player:
    """Player data."""

    def __init__(self, id: str, player_number: int, websocket):
        """Initialize the player data."""
        self.id = str(id)
        self.websocket = websocket
        self.player_number = player_number
        self.score = 0
        self.paddle_position = (0, 0)
        self.paddle_size = (10, 100)

    def to_dict(self):
        """Return a dict with the player data.

        Returns:
            dict: The player data.
        """
        data = {
            'position': self.paddle_position,
            'score': self.score,
            'player_number': self.player_number,
            'paddle_size': self.paddle_size
        }
        return data


class Brick:
    def __init__(self, position_x: int, position_y: int, size: tuple = (10, 50)):
        self.size = size
        self.position = (position_x, position_y)
        self.points = 1


class Bricks:
    def __init__(self, screen_size, server_reference):
        self.screen_size = screen_size
        self.brick_list = self.generate_bricks()
        self.server = server_reference

    def generate_bricks(self):
        brick_list = []
        y_offset = 150
        x_offset = 0
        for r in range(1, 5):
            brick = Brick(self.screen_size[0]//2, y_offset * r)
            x_offset += 100
            brick_list.append(brick)

        return brick_list

    def to_json(self):
        data = []
        for position, brick in enumerate(self.brick_list):
            data.append({"position": brick.position})
        return data

        # data = [list(brick.position) for brick self.brick_list]
        # return data



class Server:
    """The pong game server."""

    def __init__(self):
        """Initialize the player and ball data."""
        self.last_client_bounced: Player = None  # The paddle that the ball last bounced off of
        self.active_clients: dict[int, Player] = {}
        self.client_websockets = []
        # Ball variables
        self.max_players = 4
        self.screen_size = (700, 700)
        self.paddle_size = (10, 100)
        self.ball = Ball(self.screen_size, self)
        self.bricks = Bricks(self.screen_size, self)


    async def main(self):
        """Process a game loop tick."""
        async with websockets.serve(self.handler, '0.0.0.0', 8765):
            while True:
                await self.game_update()
                await self.broadcast_updates()
                await asyncio.sleep(1 / 60)

    async def handler(self, websocket):
        """Handle websocket connections."""
        try:
            if len(self.active_clients) >= self.max_players:
                await websocket.close(reason="Only four players at once.")

            self.client_websockets.append(websocket)
            player = Player(websocket.id, len(self.active_clients), websocket)
            self.active_clients[player.player_number] = player
            async for message in websocket:
                event = json.loads(message)
                if event['type'] == 'init':
                    data = {
                        'type': 'join',
                        'data': {
                            'new': player.player_number,
                            'ingame': list(self.active_clients.keys())
                        }
                    }
                    websockets.broadcast(
                        self.client_websockets,
                        json.dumps(data)
                    )
                elif event['type'] == 'paddle':
                    # Paddle position update
                    player.paddle_position = event['data']
        finally:
            # Clean up the connection
            await websocket.close()
            self.client_websockets.remove(websocket)
            del self.active_clients[player.player_number]  # Clear client num
            websockets.broadcast(
                self.client_websockets,
                json.dumps({'type': 'leave', 'data': player.player_number})
            )

    def reset_ball(self):
        """Reset the ball position."""
        self.ball_position = self.ball_position_start
        self.ball_speed = self.ball_speed_start

    async def game_update(self):
        if self.active_clients:
            await self.ball.update_ball_position()

    def add_score(self, points: int = 1):
        """Update the score."""
        if self.last_client_bounced is not None:
            self.last_client_bounced.score += points

    async def broadcast_updates(self):
        """Broadcast updates to each connected client."""
        players = {player.player_number: player.to_dict() for player in self.active_clients.values()}
        updates = {
            'type': 'updates',
            'data': {
                'players': players,
                'bricks': self.bricks.to_json(),
                'ball': self.ball.ball_position,
                'bounce': self.ball.ball_bounced,
            }
        }
        print(updates)
        websockets.broadcast(self.client_websockets, json.dumps(updates))


if __name__ == '__main__':
    server = Server()
    asyncio.run(server.main())
