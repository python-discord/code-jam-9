# Pongout

A Pong/Breakout hybrid with some odd features and twists.

This repository contains the **Zesty Zombies** team's submission for the [9th Python Discord Code Jam](https://www.pythondiscord.com/events/code-jams/9/).

## Table of Contents

- [Pongout](#pongout)
  - [Table of Contents](#table-of-contents)
  - [Playing the Game](#playing-the-game)
    - [Requirements](#requirements)
    - [Launching the Client](#launching-the-client)
    - [Gameplay](#gameplay)
    - [Hosting a Server](#hosting-a-server)
    - [Docker](#docker)
    - [Extras](#extras)
  - [How It Works](#how-it-works)
    - [Communication](#communication)
    - [User Interface](#user-interface)
  - [Improvements](#improvements)
  - [Credits](#credits)
  - [License](#license)

## Playing the Game

### Requirements

- [Python 3.10](https://www.python.org/downloads/) or newer

### Launching the Client

Clone or download the code in this repository.

Create a virtual environment in the same directory as the code.

```bash
python -m venv .venv
```

Activate the virtual environment.

```bash
# PowerShell
.venv/Scripts/activate
# Command Prompt
.venv\Scripts\activate
# Bash or other Linux shell
source .venv/bin/activate
```

Install the dependencies.

```bash
pip install -r requirements.txt
```

Run the client.

```bash
python client.py
```

Enter the IP address of a server to connect to.

![image](https://user-images.githubusercontent.com/49930425/182553749-e0cee289-c3f6-4559-9dfa-f0474b62463a.png)

Click the Connect button to join the server and start playing. Multiple clients can be run on the same machine.

Note: The text field does not show a cursor or highlight text, but you are still able to type in it.

A public server will be available during the Code Jam for judging and demonstration purposes at the IP address `zesty-zombies.pshome.me`.

### Gameplay

The goal of the game is to prevent the ball from going past your paddle and hitting the wall behind it. Move the paddle with your mouse cursor to hit the ball on the screen. Up to 4 players can join a server, each controlling a paddle on one of the edges of the screen. The ball will bounce off walls where no paddle is present.

Points are awarded to the player who last bounced the ball before it hits a wall and is reset.

Bricks will spawn randomly on the field. Extra points are awarded for each brick destroyed. There is a small chance for a brick to activate a powerup when it is destroyed.

Powerups affect every player *except* the player who activated it, and last for a short period of time. There are three types of powerups:

- Invisible Ball: The ball becomes nearly invisible.
- Invisible Paddle: All paddles become nearly invisible.
- Inverted Paddle Movement: Your paddle will move in the opposite direction from your mouse cursor.

### Hosting a Server

Follow the steps to download the code, create a virtual environment, and install the dependencies from [Launching the Client](#launching-the-client).

Run the server.

```bash
python server.py
```

This will start a server on the IP address `0.0.0.0` and port `8765`.

If you want the server to be accessible from the Internet, you need to port-forward port `8765`. This process is similar to hosting a Minecraft server locally. Otherwise the server will be available on the local network only.

### Docker

The repository contains a Dockerfile if you wish to run the server in a container.

Build the container image.

```bash
docker build -t zesty_zombies .
```

Run the container.

```bash
docker run -d -p 8765:8765 --name="zesty_zombies" zesty-zombies
```

This will expose port 8765 to be connected to, additional firewall configuration and port-forwarding may be required.

### Extras

There are some extra ~~bugs~~ features included in the game, but we will not list them here. Have fun finding them!

## How It Works

### Communication

The client and server communicate using [WebSockets](https://pypi.org/project/websockets/) by sending data in JSON format.

The client sends messages to update the server with its current paddle position.

```json
{
  "type": "paddle", // Paddle position update message
  "data": [0, 0] // Paddle coordinates
}
```

The client also sends an `init` message to notify the server that it would like to join.

```json
{
  "type": "init" // Server join request message
}
```

The server broadcasts messages containing the game state to all clients continuously.

```json
{
    "type": "updates", // Game state update message
    "data": {
        "ball": [0, 0], // Ball coordinates
        "ball_texture": 0, // Ball texture index
        "bounce": false, // Whether the ball has bounced
        "players": { // Dict of players in the game
            "0": { // Player number
                "position": [0, 0], // Player coordinates
                "score": 0, // Player score
                "player_number": 0, // Player number
                "paddle_size": [10, 100] // Paddle size
            },
            ...
        },
        "bricks": [ // List of bricks on the field
            {
                "position": [0, 0], // Brick coordinates
                "size": [10, 50] // Brick size
            },
            ...
        ],
        "powerups": [ // List of active powerups
            {
                "type": "Powerup", // Powerup type
                "user": 0 // Player that activated the powerup
            },
            ...
        ]
    }
}
```

The server also broadcasts events.

```json
{
    "type": "join", // Player join event message
    "data": {
        "new": 2, // Number of the new player
        "ingame": [0, 1] // List of connected players
    }
}

```

```json
{
    "type": "leave", // Player leave event message
    "data": 0 // Number of the player who left
}
```

```json
{
    "type": "new_powerup", // Powerup activation event message
    "data": {
        "type": "Powerup", // Powerup type
        "user": 0 // Player that activated the powerup
    }
}
```

### User Interface

The client uses the [`arcade`](https://pypi.org/project/arcade/) library to show the game state on screen and get the mouse cursor position.

## Improvements

The Code Jam submission deadline has passed, however the game can still be improved outside of the Code Jam. These are some improvements that could be made:

- [ ] General code cleanup
- [ ] Performance improvements
- [ ] Unified JSON message format
- [ ] CRT filter effect
- [ ] Player names
- [ ] DPI aware rendering
- [ ] Support for multiple balls

As well as some minor fixes:

- [ ] Adjust balancing of invisibility powerups
- [ ] Center the client window on start

## Credits

The **Zesty Zombies** team consists of the following members:

- [nitinramvelraj](https://github.com/nitinramvelraj) (team leader)
- [LemonPi314](https://github.com/LemonPi314)
- [pmsharp2](https://github.com/pmsharp2)
- [ilcheese2](https://github.com/ilcheese2)
- [striker4150](https://github.com/striker4150)

## License

This code is licensed under the [MIT license](LICENSE).

Assets in the `images` directory are licensed under the [MIT license](LICENSE) and created by [LemonPi314](https://github.com/LemonPi314).
