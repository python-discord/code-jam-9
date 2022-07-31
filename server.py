"""The server code."""

import asyncio
import json
import random

import websockets

from ball import Ball

BRICK_PATTERNS = {
    'plus_pattern': [
        [0.25, 0.50, 50, 10],
        [0.35, 0.50, 50, 10],
        [0.65, 0.50, 50, 10],
        [0.75, 0.50, 50, 10],
        [0.50, 0.25, 10, 50],
        [0.50, 0.35, 10, 50],
        [0.50, 0.65, 10, 50],
        [0.50, 0.75, 10, 50],
        [0.45, 0.50, 10, 50],
        [0.55, 0.50, 10, 50],
        [0.50, 0.45, 50, 10],
        [0.50, 0.55, 50, 10],
    ],
    'cross_pattern': [
        [0.50, 0.65, 50, 10],
        [0.45, 0.60, 10, 50],
        [0.55, 0.60, 10, 50],
        [0.40, 0.55, 50, 10],
        [0.60, 0.55, 50, 10],
        [0.35, 0.50, 10, 50],
        [0.65, 0.50, 10, 50],
        [0.40, 0.45, 50, 10],
        [0.60, 0.45, 50, 10],
        [0.45, 0.40, 10, 50],
        [0.55, 0.40, 10, 50],
        [0.50, 0.35, 50, 10],
    ],
    'x_pattern': [
        [0.25, 0.75, 50, 10],
        [0.25, 0.75, 10, 50],
        [0.75, 0.75, 50, 10],
        [0.75, 0.75, 10, 50],
        [0.37, 0.63, 50, 10],
        [0.37, 0.63, 10, 50],
        [0.63, 0.63, 50, 10],
        [0.63, 0.63, 10, 50],
        [0.50, 0.50, 50, 10],
        [0.50, 0.50, 10, 50],
        [0.37, 0.37, 50, 10],
        [0.37, 0.37, 10, 50],
        [0.63, 0.37, 50, 10],
        [0.63, 0.37, 10, 50],
        [0.25, 0.25, 50, 10],
        [0.25, 0.25, 10, 50],
        [0.75, 0.25, 50, 10],
        [0.75, 0.25, 10, 50],
    ],
    'smile': [
        [0.25, 0.75, 50, 10],
        [0.25, 0.75, 10, 50],
        [0.75, 0.75, 50, 10],
        [0.75, 0.75, 10, 50],
        [0.25, 0.45, 10, 50],
        [0.30, 0.40, 50, 10],
        [0.35, 0.35, 10, 50],
        [0.40, 0.30, 50, 10],
        [0.45, 0.25, 10, 50],
        [0.50, 0.20, 50, 10],
        [0.75, 0.45, 10, 50],
        [0.70, 0.40, 50, 10],
        [0.65, 0.35, 10, 50],
        [0.60, 0.30, 50, 10],
        [0.55, 0.25, 10, 50],
    ]
}


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

    def to_dict(self) -> dict:
        """Return a dict with the player data.

        Returns:
            dict: The player data.
        """
        data = {
            'position': self.paddle_position,
            'score': self.score,
            'player_number': self.player_number,
            'paddle_size': self.paddle_size,
        }
        return data


class Powerup:
    def __init__(self):
        pass

    def apply(self, server, player: Player, timer=5):
        self.user = player
        self.timer = timer * 60
        server.powerups.append(self)
        data = {
            'type': 'new_powerup',
            'data': {
                'user': player.player_number,
                'type': self.__class__.__name__,
            },
        }
        websockets.broadcast(server.client_websockets, json.dumps(data))  # type: ignore

    def to_json(self):
        return {"type": self.__class__.__name__, "user": self.user.player_number}


class InvisiblePaddlePowerup(Powerup):
    pass


class InvisibleBallPowerup(Powerup):
    pass


class InvertedPaddlePowerup(Powerup):
    pass


class Brick:

    def __init__(self, position_x: int, position_y: int, size: tuple = (10, 50)):
        self.size = size
        self.position = (position_x, position_y)
        self.powerups = [InvisiblePaddlePowerup, InvisibleBallPowerup, InvertedPaddlePowerup]
        self.powerup_chance = 5

    def get_powerup(self):
        if random.randint(1, self.powerup_chance) == 1:
            return random.choice(self.powerups)()


class Bricks:
    def __init__(self, screen_size, server):
        self.screen_size = screen_size
        self.brick_list: list[Brick] = []
        self.server = server
        self.generate_based_on_pattern()

    def generate_based_on_pattern(self):
        pattern = random.choice(list(BRICK_PATTERNS.values()))
        for p in pattern:
            self.brick_list.append(
                Brick(
                    self.screen_size[0] * p[0],
                    self.screen_size[1] * p[1],
                    (p[2], p[3]),
                )
            )

    def delete_brick(self, brick: Brick, player: Player):
        powerup = brick.get_powerup()
        if powerup is not None:
            powerup.apply(self.server, player)
        self.brick_list.remove(brick)

    def to_json(self):
        data = []
        for brick in self.brick_list:
            data.append({"position": brick.position, "size": brick.size})
        return data

    def empty_bricks(self):
        self.brick_list = []


class Server:
    """The pong game server."""

    def __init__(self, screen_size: tuple[int, int] = (700, 700), max_players: int = 4):
        """Initialize the player and ball data."""
        self.screen_size = screen_size
        self.max_players = max_players
        self.active_clients: dict[int, Player] = {}
        self.client_websockets = []
        self.paddle_size = (10, 100)
        self.ball = Ball(self.screen_size, self)
        self.bricks = Bricks(self.screen_size, self)
        self.powerups: list[Powerup] = []
        self.last_client_bounced = None

    def run(self):
        asyncio.run(self.main())

    async def main(self):
        """Process a game loop tick."""
        async with websockets.serve(self.handler, '0.0.0.0', 8765):  # type: ignore
            while True:
                self.game_update()
                await self.broadcast_updates()
                await asyncio.sleep(1 / 60)

    async def handler(self, websocket):
        """Handle websocket connections."""
        if len(self.active_clients) >= self.max_players:
            await websocket.close(reason="Only four players at once.")

        self.client_websockets.append(websocket)
        player = Player(websocket.id, len(self.active_clients), websocket)
        self.active_clients[player.player_number] = player
        try:
            async for message in websocket:
                event = json.loads(message)
                if event['type'] == 'init':
                    data = {
                        'type': 'join',
                        'data': {
                            'new': player.player_number,
                            'ingame': [k for k in self.active_clients.keys() if k != player.player_number],
                        },
                    }
                    websockets.broadcast(self.client_websockets, json.dumps(data))  # type: ignore
                elif event['type'] == 'paddle':
                    # Paddle position update
                    player.paddle_position = event['data']
        finally:
            # Clean up the connection
            await websocket.close()
            self.client_websockets.remove(websocket)
            del self.active_clients[player.player_number]  # Clear client num
            if self.last_client_bounced == player.player_number:
                self.last_client_bounced = None
            websockets.broadcast(  # type: ignore
                self.client_websockets,
                json.dumps({'type': 'leave', 'data': player.player_number}),
            )

    def add_score(self, side_bounced, points: int = 1):
        """Update the score."""
        if self.last_client_bounced is not None and self.last_client_bounced != side_bounced:
            self.last_client_bounced.score += points

    def game_update(self):
        if self.active_clients:
            self.ball.update_position()
        powerups = []
        for powerup in self.powerups:
            powerup.timer -= 1
            if powerup.timer > 0:
                powerups.append(powerup)
        self.powerups = powerups

    async def broadcast_updates(self):
        """Broadcast updates to each connected client."""
        players = {player.player_number: player.to_dict() for player in self.active_clients.values()}
        updates = {
            'type': 'updates',
            'data': {
                'players': players,
                'bricks': self.bricks.to_json(),
                'ball': self.ball.position,
                'ball_texture': self.ball.texture,
                'bounce': self.ball.bounced,
                'powerups': [powerup.to_json() for powerup in self.powerups],
            },
        }
        websockets.broadcast(self.client_websockets, json.dumps(updates))  # type: ignore


if __name__ == '__main__':
    server = Server()
    server.run()
