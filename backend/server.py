"""The server code."""

import asyncio
import json

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

    def to_dict(self) -> dict:
        """Return a dict with the player data.

        Returns:
            dict: The player data.
        """
        data = {
            'position': self.paddle_position,
            'score': self.score,
            'player_number': self.player_number
        }
        return data


class Server:
    """The pong game server."""

    def __init__(self, screen_size: tuple[int, int] = (700, 700), max_players: int = 4):
        """Initialize the player and ball data."""
        self.last_client_bounced: Player = None  # The paddle that the ball last bounced off of
        self.last_collided_side: int = 0
        self.active_clients: dict[int, Player] = {}
        self.client_websockets = []
        # Ball variables
        self.max_players = max_players
        self.screen_size: tuple[int, int] = screen_size
        self.paddle_size: tuple[int, int] = (10, 100)
        self.ball_size: tuple[int, int] = (10, 10)
        self.ball_position_start: tuple[int, int] = (self.screen_size[0] // 2, self.screen_size[1] // 2)
        self.ball_position: tuple[int, int] = self.ball_position_start
        self.ball_speed_start: tuple[int, int] = (5, 5)
        self.ball_speed: tuple[int, int] = self.ball_speed_start
        self.ball_bounced: bool = False
        self.ball_last_side_bounced_off_of = None

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
                            'ingame': [k for k in self.active_clients.keys() if k != player.player_number],
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

    def add_score(self):
        """Update the score."""
        if self.last_client_bounced is not None:
            self.last_client_bounced.score += 1

    async def game_update(self):
        """Handle game calculations."""
        collided_side = None
        ball_x = self.ball_position[0]
        ball_y = self.ball_position[1]

        # Check if ball collides with a wall
        if ball_x <= 0 and self.last_collided_side != 0:
            if self.active_clients.get(0) is not None:
                self.add_score()
                self.reset_ball()
            else:
                collided_side = 0

        if ball_x >= self.screen_size[0] and self.last_collided_side != 1:
            if self.active_clients.get(1) is not None:
                self.add_score()
                self.reset_ball()
            else:
                collided_side = 1

        if ball_y <= 0 and self.last_collided_side != 2:
            if self.active_clients.get(2) is not None:
                self.add_score()
                self.reset_ball()
            else:
                collided_side = 2

        if ball_y >= self.screen_size[1] and self.last_collided_side != 3:
            if self.active_clients.get(3) is not None:
                self.add_score()
                self.reset_ball()
            else:
                collided_side = 3

        # Check if ball collides with a paddle
        if collided_side is None:
            for client in self.active_clients.values():
                if self.check_ball_paddle_collision(client.paddle_position, client.player_number):
                    collided_side = client.player_number
                    self.last_client_bounced = client
                    break

        # Ball collision logic
        if collided_side is not None:
            self.ball_bounced = True
            self.last_collided_side = collided_side
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

    def check_ball_paddle_collision(self, paddle_pos: tuple[int, int], player_number: int) -> bool:
        """Check if the ball is colliding with a paddle."""
        bx1 = self.ball_position[0] + self.ball_size[0] // 2
        by1 = self.ball_position[1] + self.ball_size[1] // 2
        bx2 = self.ball_position[0] - self.ball_size[0] // 2
        by2 = self.ball_position[1] - self.ball_size[1] // 2
        if player_number >= 2:
            px1 = paddle_pos[0] + self.paddle_size[1] // 2
            py1 = paddle_pos[1] + self.paddle_size[0] // 2
            px2 = paddle_pos[0] - self.paddle_size[1] // 2
            py2 = paddle_pos[1] - self.paddle_size[0] // 2
        else:
            px1 = paddle_pos[0] + self.paddle_size[0] // 2
            py1 = paddle_pos[1] + self.paddle_size[1] // 2
            px2 = paddle_pos[0] - self.paddle_size[0] // 2
            py2 = paddle_pos[1] - self.paddle_size[1] // 2
        return not (
            bx1 < px2
            or bx2 > px1
            or by2 > py1
            or by1 < py2
        )

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
