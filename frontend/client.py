"""The client code."""
import asyncio
import json
import os
import threading

# Suppress pygame's hello message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame  # noqa: E402
import pygame_menu  # noqa: E402
import websockets  # noqa: E402
from pygame.locals import QUIT  # noqa: E402

SCREEN_WIDTH = 700
SCREEN_HEIGHT = 700
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 100
FPS = 60
ANGLE_MULTIPLIER = 75


def clamp(value, min_value, max_value):
    """Restrict the provided value to be between a minimum and maximum."""
    return min(max(value, min_value), max_value)


def lerp(value, new_value, multiplier):
    """Do linear interpolation on the provided value."""
    return value + (multiplier * (new_value - value))


class Paddle(pygame.sprite.Sprite):
    """The paddle sprite."""

    def __init__(self, direction=1, size=(PADDLE_WIDTH, PADDLE_HEIGHT), number=0, local=True):
        """Initialize a paddle sprite.

        Args:
            direction (int, optional): Determines whether the paddle is vertical or horizontal. Defaults to 1.
            size (tuple, optional): The dimensions of the paddle sprite. Defaults to (PADDLE_WIDTH, PADDLE_HEIGHT).
            number (int, optional): The paddle number. Defaults to 0.
            local (bool, optional): Set to True if the paddle movement is controlled by the client. Defaults to True.
        """
        super().__init__()
        self.direction = direction
        self.size = size
        self.number = number
        if self.number > 1:
            self.direction = 0
        if self.direction == 0:
            self.size = (size[1], size[0])
        self.local = local
        self.image = pygame.Surface(self.size)
        self.image.fill((255, 255, 255))
        self.rect = self.image.get_rect()
        if self.number == 0:
            self.rect.centerx = 30
        elif self.number == 1:
            self.rect.centerx = SCREEN_WIDTH - 30
        elif self.number == 2:
            self.rect.centery = 30
        elif self.number == 3:
            self.rect.centery = SCREEN_HEIGHT - 30

    def update(self, players):
        """Update the paddle location.

        Args:
            players (dict): A dict containing the players.
        """
        if self.local:
            mouse_pos = pygame.mouse.get_pos()[self.direction]  # Mouse y value
            if self.direction == 0:
                self.rect.centerx = clamp(mouse_pos, self.rect.width / 2, SCREEN_WIDTH - self.rect.width / 2)
            else:
                self.rect.centery = clamp(mouse_pos, self.rect.height / 2, SCREEN_HEIGHT - self.rect.height / 2)
        else:
            try:
                self.rect.center = players[self.number]['position']
            except KeyError:  # Hack because dict does not get populated fast enough
                pass


class Ball(pygame.sprite.Sprite):
    """The ball sprite."""

    def __init__(self, size=(10, 10)):
        """Initialize a ball sprite.

        Args:
            size (tuple, optional): The dimensions of the ball sprite. Defaults to (10, 10).
        """
        super().__init__()
        self.image = pygame.Surface(size)
        self.image.fill((255, 255, 255))
        self.rect = self.image.get_rect()

    def update(self, position, mps):
        """Update the ball location.

        Args:
            position (tuple): The XY coordinates of the ball.
        """
        self.rect.center = position
        # if mps == 0:
        #     self.rect.center = position
        # else:
        #     self.rect.center = (
        #         lerp(self.rect.centerx, position[0], FPS / mps),
        #         lerp(self.rect.centery, position[1], FPS / mps)
        #     )

class Brick(pygame.sprite.Sprite):

    def __init__(self, size=(10, 50)):
        """The Brick sprite."""

        super().__init__()
        self.image = pygame.Surface(size)
        self.image.fill((255, 255, 255))
        self.rect = self.image.get_rect()
    
    def update(self, message):

        self.rect.center = message['position']


class Client:
    """The pong game client."""

    def __init__(self):
        """Initialize the client."""
        self.player_number = None
        self.updates = None
        self.paddles: dict[int, Paddle] = {}
        self.bricks: list[Brick] = []
        self.start_event = threading.Event()
        self.stop_event = threading.Event()
        self.mps = 0  # Messages per second
        self.average_mps = 0

    async def network_loop(self):
        """Manage the game networking."""
        try:
            async with websockets.connect('ws://localhost:8765') as websocket:
                await websocket.send(json.dumps({'type': 'init'}))
                while self.player_number is None:
                    message = json.loads(await websocket.recv())
                    if message['type'] == 'join':
                        self.player_number = message['data']['new']
                        for number in message['data']['ingame']:
                            self.paddles[number] = Paddle(number=number, local=False)
                self.start_event.set()
                while True:
                    data = {'type': 'paddle', 'data': self.paddles[self.player_number].rect.center}
                    await websocket.send(json.dumps(data))
                    message = json.loads(await websocket.recv())
                    self.mps += 1
                    if message['type'] == 'join':
                        self.paddles[message['data']['new']] = Paddle(number=message['data']['new'], local=False)
                    elif message['type'] == 'leave':
                        del self.paddles[message['data']]
                    elif message['type'] == 'updates':
                        updates = message['data']
                        # Convert keys back to ints because yes
                        updates['players'] = {int(k): v for k, v in updates['players'].items()}
                        self.updates = updates
                        if not len(updates['bricks']) == len(self.bricks):
                            self.bricks = []
                            for brick in updates['bricks']:
                                print(brick)
                                self.bricks.append(Brick(brick['size']))
        except websockets.ConnectionClosed:
            self.stop_event.set()

    def start_game(self, screen):
        """Run the game.

        Args:
            screen (pygame.Surface): The game screen.
        """
        ball = Ball()
        local_paddle = Paddle(number=self.player_number)
        self.paddles[self.player_number] = local_paddle
        clock = pygame.time.Clock()
        counter = 0
        while True:
            if self.stop_event.is_set():
                raise SystemExit
            events = pygame.event.get()
            for event in events:
                if event.type == QUIT:
                    raise SystemExit
            screen.fill((0, 0, 0))
            ball.update(self.updates['ball'], self.average_mps)
            screen.blit(ball.image, ball.rect)
            for paddle in self.paddles.values():
                paddle.update(self.updates['players'])
            screen.blits([(paddle.image, paddle.rect) for paddle in self.paddles.values()])
            for index, brick in enumerate(self.bricks):
                brick.update(self.updates['bricks'][index])
            screen.blits([(brick.image, brick.rect) for brick in self.bricks])
            pygame.display.flip()  # Updates the display
            clock.tick(FPS)
            counter += 1
            if counter == FPS:
                self.average_mps = self.mps if self.average_mps == 0 else int(sum([self.mps, self.average_mps]) / 2)
                self.mps = 0
                counter = 0

    def menu(self, screen):
        """Display the start menu.

        Args:
            screen (pygame.Surface): The game screen.
        """
        menu = pygame_menu.Menu('Welcome', 400, 300, theme=pygame_menu.themes.THEME_BLUE)

        menu.add.text_input('Name :', default='John Doe')
        menu.add.button('Play', self.start_game, screen)
        menu.add.button('Quit', pygame_menu.events.EXIT)
        menu.mainloop(screen)

    async def main(self):
        """Start the game client."""
        self.network_thread = threading.Thread(target=lambda: asyncio.run(self.network_loop()), daemon=True)
        self.network_thread.start()
        self.start_event.wait()
        pygame.init()
        screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
        self.menu(screen)


if __name__ == '__main__':
    client = Client()
    asyncio.run(client.main())
