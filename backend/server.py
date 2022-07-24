"""The server code."""

import asyncio
import json

import websockets

MAX_PLAYERS = 4
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 100


class Player:
    def __init__(self, id: str, player_number: int, websocket):
        self.id = str(id)
        self.websocket = websocket
        self.player_number = player_number
        self.score = 0
        self.paddle_position = (0, 0)

    def to_dict(self):
        data = {
            'position': self.paddle_position,
            'score': self.score,
            'player_number': self.player_number
        }
        return data


class Server:
    """The pong game server."""

    def __init__(self):
        """Initialize the player and ball data."""
        self.last_client_bounced: Player = None  # The paddle that the ball last bounced off of
        self.active_clients: dict[int, Player] = {}
        self.client_websockets = []
        # Ball variables
        self.ball_position_start: tuple[int, int] = (100, 100)
        self.ball_position: tuple[int, int] = (100, 100)
        self.ball_speed_start: tuple[int, int] = (2, 2)
        self.ball_speed: tuple[int, int] = (2, 2)
        self.ball_bounced: bool = False

    async def main(self):
        """Process a game loop tick."""
        async with websockets.serve(self.handler, 'localhost', 8765):
            while True:
                await self.game_update()
                await self.broadcast_updates()
                await asyncio.sleep(1 / 60)

    async def handler(self, websocket):
        """Handle websocket connections."""
        try:
            if len(self.active_clients) >= MAX_PLAYERS:
                await websocket.close(reason="Only four players at once.")

            player = Player(websocket.id, len(self.active_clients), websocket)
            self.client_websockets.append(websocket)
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
        """Handle game calculations."""
        collided_side = None
        ball_x = self.ball_position[0]
        ball_y = self.ball_position[1]

        # Check if ball collides with a wall
        if ball_x <= 0:
            if self.active_clients.get(0) is not None:
                self.add_score()
                self.reset_ball()
            else:
                collided_side = 0
        if ball_x >= SCREEN_WIDTH:
            if self.active_clients.get(1) is not None:
                self.add_score()
                self.reset_ball()
            else:
                collided_side = 1
        if ball_y <= 0:
            if self.active_clients.get(2) is not None:
                self.add_score()
                self.reset_ball()
            else:
                collided_side = 2
        if ball_y >= SCREEN_HEIGHT:
            if self.active_clients.get(3) is not None:
                self.add_score()
                self.reset_ball()
            else:
                collided_side = 3

        # Check if ball collides with a paddle
        if collided_side is None:
            for client in self.active_clients.values():
                if self.check_ball_paddle_collision(client.paddle_position):
                    collided_side = client.player_number
                    self.last_client_bounced = client
                    break

        # Ball collision logic
        if collided_side is not None:
            self.ball_bounced = True
            # Calculate new ball speed
            if collided_side == 0:
                self.ball_speed = (-self.ball_speed[0], self.ball_speed[1])
            if collided_side == 1:
                self.ball_speed = (-self.ball_speed[0], self.ball_speed[1])
            if collided_side == 2:
                self.ball_speed = (self.ball_speed[0], -self.ball_speed[1])
            if collided_side == 3:
                self.ball_speed = (self.ball_speed[0], -self.ball_speed[1])
        else:
            self.ball_bounced = False

        # Update the ball position
        self.ball_position = (
            self.ball_position[0] + self.ball_speed[0],
            self.ball_position[1] + self.ball_speed[1]
        )

    def check_ball_paddle_collision(self, paddle):
        """Check if the ball is colliding with a paddle."""
        bx = self.ball_position[0]
        by = self.ball_position[1]
        px1 = paddle[0]
        py1 = paddle[1]
        px2 = px1 + PADDLE_WIDTH
        py2 = py1 + PADDLE_HEIGHT
        collision = (
            ((px1 >= bx >= px2) or (px2 >= bx >= px1))
            and ((py1 >= by >= py2) or (py2 >= by >= py1))
        )
        return collision

    def add_score(self):
        """Update the score."""
        if self.last_client_bounced is not None:
            self.last_client_bounced.score += 1

    async def broadcast_updates(self):
        """Broadcast updates to each connected client."""
        players = {player.player_number: player.to_dict() for player in self.active_clients.values()}
        updates = {
            'type': 'updates',
            'data': {
                'players': players,
                'ball': self.ball_position,
                'bounce': self.ball_bounced,
            }
        }
        websockets.broadcast(self.client_websockets, json.dumps(updates))


if __name__ == '__main__':
    server = Server()
    asyncio.run(server.main())
