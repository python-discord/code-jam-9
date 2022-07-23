"""The server code."""

import asyncio
import json

import websockets

MAX_PLAYERS = 4

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

PADDLE_LENGTH = 100
PADDLE_WIDTH = 10


class Player:
    def __init__(self, client_id, player_number, connection):
        self.client_id = client_id
        self.connection = connection
        self.player_number = player_number
        self.score = 0
        self.paddle_position = (0, 0)

    def to_json(self):
        data = {self.player_number: {
            "position": self.paddle_position,
            "score": self.score
        }}
        return json.dumps(data)


class Server:
    """The pong game server."""

    def __init__(self):
        """Initialize the player and ball data."""
        self.last_paddle_bounced = None  # The paddle that the ball last bounced off of
        # Values stored according to player order
        self.active_clients = {}

        # Ball variables
        self.ball_position = (0, 0)
        self.ball_speed = (1, 1)
        self.ball_bounced = False

    async def handler(self, websocket):
        """Handle websocket connections."""
        if len(self.active_clients) >= MAX_PLAYERS:
            await websocket.close(reason="Only four players at once!")

        player = Player(websocket.id, len(self.active_clients), websocket)
        self.active_clients[player.client_id] = player
        await websocket.send(json.dumps({
            "type": "info",
            "data": {
                "screen_width": SCREEN_WIDTH,
                "screen_height": SCREEN_HEIGHT,
                "paddle_length": PADDLE_LENGTH,
                "paddle_width": PADDLE_WIDTH,
                "paddle_num": len(self.active_clients) - 1
            }
        }))
        async for message in websocket:
            event = json.loads(message)

            # print(websocket.id, event)  # DEBUG

            if event["type"] == "paddle":
                # Paddle position update
                self.paddle_update_handler(player, event["data"])
                # await player.connection.send(json.dumps(player.paddle_position))
        # Clean up the connection
        del self.active_clients[websocket.id] # Clear client num

    async def main(self):
        """Process a game loop tick."""
        async with websockets.serve(self.handler, "localhost", 8765):
            while True:
                await asyncio.sleep(1 / 60)
                await self.game_update()
                await self.broadcast_updates()

    def reset_ball(self):
        """Reset the ball position."""
        self.ball_position = (0, 0)

    async def game_update(self):
        """Handle game calculations."""
        collided_side = None
        paddle_collision = False
        ball_x = self.ball_position[0]
        ball_y = self.ball_position[1]

        # Check if ball collides with a wall
        if ball_x <= 0:
            if len(self.active_clients) > 0:
                self.client_from_side(self.last_paddle_bounced).score += 1
                self.reset_ball()
            else:
                collided_side = 0
        if ball_x >= SCREEN_WIDTH:
            if len(self.active_clients) > 1:
                self.client_from_side(self.last_paddle_bounced).score += 1
                self.reset_ball()
            else:
                collided_side = 1
        if ball_y <= 0:
            if len(self.active_clients) > 2:
                self.client_from_side(self.last_paddle_bounced).score += 1
                self.reset_ball()
            else:
                collided_side = 2
        if ball_y >= SCREEN_HEIGHT:
            if len(self.active_clients) > 3:
                self.client_from_side(self.last_paddle_bounced).score += 1
                self.reset_ball()
            else:
                collided_side = 3

        # Check if ball collides with a paddle
        if collided_side is None:
            collision_result = self.check_ball_collision()
            if(collision_result is not None):
                paddle_collision = True
                collided_side = collision_result

        # Ball collision logic
        if collided_side is not None:
            # Set most recent paddle collision
            if paddle_collision:
                self.last_paddle_bounced = collided_side
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
        self.ball_position = (ball_x + self.ball_speed[0], self.ball_position[1] + self.ball_speed[1])


    def paddle_update_handler(self, player, new_location):
        """Update the specified paddle location."""
        player.paddle_position = new_location

    def check_ball_collision(self):
        """
        Check if the ball collided with a paddle.

        Returns the number of the paddle it collided, and returns None if no collision occurred.
        """
        ball_x = self.ball_position[0]
        ball_y = self.ball_position[1]
        clients = [self.client_from_side(i) for i in range(4)]
        if (ball_y >= clients[0].paddle_position[1]
                and ball_y <= clients[0].paddle_position[1] + PADDLE_LENGTH
                and ball_x <= clients[0].paddle_position[0]
                and ball_x >= clients[0].paddle_position[0] - PADDLE_WIDTH):
            return 0
        elif (ball_y <= clients[1].paddle_position[1]
                and ball_y >= clients[1].paddle_position[1] - PADDLE_LENGTH
                and ball_x >= clients[1].paddle_position[0]
                and ball_x <= clients[1].paddle_position[0] + PADDLE_WIDTH):
            return 1
        elif (ball_y <= clients[2].paddle_position[1]
                and ball_y >= clients[2].paddle_position[1] - PADDLE_WIDTH
                and ball_x <= clients[2].paddle_position[0]
                and ball_x >= clients[2].paddle_position[0] - PADDLE_LENGTH):
            return 2
        elif (ball_y >= clients[3].paddle_position[1]
                and ball_y <= clients[3].paddle_position[1] + PADDLE_WIDTH
                and ball_x >= clients[3].paddle_position[0]
                and ball_x <= clients[3].paddle_position[0] + PADDLE_LENGTH):
            return 3
        return None

    async def broadcast_updates(self):
        """Broadcast updates to each connected client."""
        broadcast_info = {
            "type": "broadcast",
            "data": {
                "players": [client.to_json() for client in self.active_clients.values()],
                "ball": self.ball_position,
                "bounce": self.ball_bounced,
            }
        }
        websockets.broadcast([player.connection for player in self.active_clients.values()], json.dumps(broadcast_info))

    def client_from_side(self, side):
        """Get the client that is on the specified side"""
        for client in self.active_clients.values():
            if client.player_number == side:
                return client


if __name__ == "__main__":
    server = Server()
    asyncio.run(server.main())
