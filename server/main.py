import asyncio
import json

import websockets
from game_components.game import Game
from game_components.game_objects import Player
from schemas import ChatMessage, InitializePlayer, PlayerSchema, RegistrationSuccessful
from websockets.legacy.server import WebSocketServerProtocol

TIME_BETWEEN_ROUNDS = 10  # Seconds between each round.

connections: dict[int, WebSocketServerProtocol] = {}
game = Game()


async def initialize_player(connection: WebSocketServerProtocol) -> Player:
    """Initializes a player in the game, and returns the initialized player."""
    message = await connection.recv()
    event = InitializePlayer.parse_obj(json.loads(message))

    username = event.username
    print(message)  # TODO: remove this later.
    player = Player(username, ["spit", "bite"])

    game.add_player(player, 1, 1)
    return player


async def register(websocket: WebSocketServerProtocol) -> None:
    """Adds a player's connections to connections and removes them when they disconnect."""
    registered_player = await initialize_player(websocket)

    player_schema = PlayerSchema(
        uid=registered_player.uid,
        name=registered_player.name,
        allowed_actions=set(registered_player.allowed_actions),
    )
    registration_response = RegistrationSuccessful(
        type="registration_successful", player=player_schema
    )

    await websocket.send(registration_response.json())
    connections[registered_player.uid] = websocket

    try:
        await handler(websocket)
    finally:
        del connections[registered_player.uid]


async def handler(websocket: WebSocketServerProtocol) -> None:
    async for message in websocket:
        event = json.loads(message)
        print(event)  # TODO: remove this later.

        match event:
            case {
                "type": "chat",
                "player_name": player_name,
                "chat_message": chat_message,
            }:
                response = ChatMessage(
                    type="chat",
                    player_name=player_name,
                    chat_message=chat_message,
                )

                websockets.broadcast(connections.values(), response.json())


async def websocket_handling() -> None:
    async with websockets.serve(register, "localhost", 8765):
        await asyncio.Future()  # run forever


async def game_loop():
    """Here we run each tick of the game."""
    while True:
        await asyncio.sleep(TIME_BETWEEN_ROUNDS)
        # HANDLING EACH TICK GOES HERE.


async def main() -> None:
    await asyncio.gather(websocket_handling(), game_loop())


asyncio.run(main())
