"""The server code."""

import asyncio
import json
import random

import websockets
from ball import Ball

PATTERNS = {'plus_pattern': [[.25, .5, 50, 10, 1], [.35, .5, 50, 10, 1], [.65, .5, 50, 10, 1], [.75, .5, 50, 10, 1],
                             [.5, .25, 10, 50, 1], [.5, .35, 10, 50, 1], [.5, .65, 10, 50, 1], [.5, .75, 10, 50, 1],
                             [.45, .5, 10, 50, 1], [.55, .5, 10, 50, 1],
                             [.5, .45, 50, 10, 1], [.5, .55, 50, 10, 1]],
            'cross_pattern': [[.5, .65, 50, 10, 1],
                              [.45, .6, 10, 50, 1], [.55, .6, 10, 50, 1],
                              [.40, .55, 50, 10, 1], [.60, .55, 50, 10, 1],
                              [.35, .5, 10, 50, 1], [.65, .5, 10, 50, 1],
                              [.40, .45, 50, 10, 1], [.60, .45, 50, 10, 1],
                              [.45, .40, 10, 50, 1], [.55, .40, 10, 50, 1],
                              [.5, .35, 50, 10, 1]],
            'x_pattern': [[.25, .75, 50, 10, 1], [.25, .75, 10, 50, 1], [.75, .75, 50, 10, 1], [.75, .75, 10, 50, 1],
                          [.37, .63, 50, 10, 1], [.37, .63, 10, 50, 1], [.63, .63, 50, 10, 1], [.63, .63, 10, 50, 1],
                          [.50, .50, 50, 10, 1], [.50, .50, 10, 50, 1],
                          [.37, .37, 50, 10, 1], [.37, .37, 10, 50, 1], [.63, .37, 50, 10, 1], [.63, .37, 10, 50, 1],
                          [.25, .25, 50, 10, 1], [.25, .25, 10, 50, 1], [.75, .25, 50, 10, 1], [.75, .25, 10, 50, 1]],
            'smile': [[.25, .75, 50, 10, 1], [.25, .75, 10, 50, 1], [.75, .75, 50, 10, 1], [.75, .75, 10, 50, 1],
                      [.25, .45, 10, 50, 1], [.30, .40, 50, 10, 1], [.35, .35, 10, 50, 1], [.40, .30, 50, 10, 1],
                      [.45, .25, 10, 50, 1], [.50, .20, 50, 10, 1],
                      [.75, .45, 10, 50, 1], [.70, .40, 50, 10, 1], [.65, .35, 10, 50, 1], [.60, .30, 50, 10, 1],
                      [.55, .25, 10, 50, 1]]
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
            'paddle_size': self.paddle_size
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
            }
        }
        websockets.broadcast(  # type: ignore
            server.client_websockets,
            json.dumps(data)
        )

    def to_json(self):
        return {"type": self.__class__.__name__, "user": self.user.player_number}


class PaddleDisappearPowerup(Powerup):
    pass


class BallDisappearPowerup(Powerup):
    pass


class InversePowerup(Powerup):
    pass


class Brick:

    powerups = [PaddleDisappearPowerup, BallDisappearPowerup, InversePowerup]
    powerup_chance = 5

    def __init__(self, position_x: int, position_y: int, size: tuple = (10, 50), points: int = 1):
        self.size = size
        self.position = (position_x, position_y)
        self.points = points

    def get_powerup(self):
        if random.randint(1, self.powerup_chance) == 1:
            return random.choice(self.powerups)()


class Bricks:

    def __init__(self, screen_size, server_reference):
        self.screen_size = screen_size
        self.brick_list = []
        self.server = server_reference

    def generate_based_on_pattern(self):
        pattern = random.choice(list(PATTERNS.values()))
        for p in pattern:
            self.brick_list.append(Brick(self.screen_size[0]*p[0],
                                         self.screen_size[1]*p[1],
                                         (p[2], p[3]),
                                         p[4]
                                         ))

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

        # data = [list(brick.position) for brick self.brick_list]
        # return data


class Server:
    """The pong game server."""

    def __init__(self, screen_size: tuple[int, int] = (700, 700), max_players: int = 4):
        """Initialize the player and ball data."""
        self.screen_size = screen_size
        self.max_players = max_players
        self.active_clients: dict[int, Player] = {}
        self.client_websockets = []
        # Ball variables
        self.max_players = 4
        self.screen_size = (700, 700)
        self.paddle_size = (10, 100)
        self.ball = Ball(self.screen_size, self)
        self.bricks = Bricks(self.screen_size, self)
        self.powerups: list[Powerup] = []
        self.last_client_bounced: Player = None

    async def main(self):
        """Process a game loop tick."""
        async with websockets.serve(self.handler, '0.0.0.0', 8765):  # type: ignore
            while True:
                await self.game_update()
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
                        }
                    }
                    websockets.broadcast(  # type: ignore
                        self.client_websockets,
                        json.dumps(data)
                    )
                elif event['type'] == 'paddle':
                    # Paddle position update
                    player.paddle_position = event['data']
        except Exception as e:
            print(e)
        finally:
            # Clean up the connection
            await websocket.close()
            self.client_websockets.remove(websocket)
            del self.active_clients[player.player_number]  # Clear client num
            if self.last_client_bounced == player.player_number:
                self.last_client_bounced = None
            websockets.broadcast(  # type: ignore
                self.client_websockets,
                json.dumps({'type': 'leave', 'data': player.player_number})
            )

    def add_to_total_bounces(self):
        self.total_bounces += 1

    def add_score(self, side_bounced, points: int = 1):
        """Update the score."""
        if self.last_client_bounced is not None and not self.last_client_bounced == side_bounced:
            self.last_client_bounced.score += points

    async def game_update(self):
        if self.active_clients:
            await self.ball.update_ball_position()
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
                'ball': self.ball.ball_position,
                'ball_texture': self.ball.texture,
                'bounce': self.ball.ball_bounced,
                'powerups': [powerup.to_json() for powerup in self.powerups]
            }
        }
        websockets.broadcast(self.client_websockets, json.dumps(updates))  # type: ignore


if __name__ == '__main__':
    server = Server()
    asyncio.run(server.main())
