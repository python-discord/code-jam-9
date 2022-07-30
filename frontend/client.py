"""The client code."""

import asyncio
import json
import os
from this import d
import threading

# Suppress pygame's hello message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame  # noqa: E402
import pygame_menu  # noqa: E402
import websockets  # noqa: E402
from pygame.locals import K_ESCAPE, KEYDOWN, QUIT  # noqa: E402

menu_theme = pygame_menu.Theme(
    background_color=(0, 0, 0, 0),
    widget_font=pygame_menu.font.FONT_MUNRO,
    title_bar_style=pygame_menu.widgets.MENUBAR_STYLE_NONE,
)


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Restrict the provided value to be between a minimum and maximum."""
    return min(max(value, min_value), max_value)


def lerp(value: float, new_value: float, multiplier: float) -> float:
    """Do linear interpolation on the provided value."""
    return value + (multiplier * (new_value - value))


class Paddle(pygame.sprite.Sprite):
    """The paddle sprite."""

    def __init__(self, size: tuple[int, int] = (10, 100), number: int = 0, direction: int = 1, local: bool = True):
        """Initialize a paddle sprite.

        Args:
            size (tuple, optional): The dimensions of the paddle sprite. Defaults to (10, 100).
            number (int, optional): The paddle number. Defaults to 0.
            direction (int, optional): Determines whether the paddle is vertical or horizontal. Defaults to 1.
            local (bool, optional): Set to True if the paddle movement is controlled by the client. Defaults to True.
        """
        super().__init__()
        self.direction = direction
        self.size = size
        self.number = number
        self.score = 0
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

    def update(self, players: dict):
        """Update the paddle location.

        Args:
            players (dict): A dict containing the players.
        """
        if self.local:
            mouse_pos = pygame.mouse.get_pos()[self.direction]
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

    def __init__(self, size: tuple[int, int] = (10, 10)):
        """Initialize a ball sprite.

        Args:
            size (tuple, optional): The dimensions of the ball sprite. Defaults to (10, 10).
        """
        super().__init__()
        self.image = pygame.Surface(size)
        self.image.fill((255, 255, 255))
        self.rect = self.image.get_rect()

    def update(self, position: tuple[int, int], mps):
        """Update the ball location.

        Args:
            position (tuple): The XY coordinates of the ball.
        """
        self.rect.center = position
        # Disabled lerp
        # if mps == 0:
        #     self.rect.center = position
        # else:
        #     self.rect.center = (
        #         lerp(self.rect.centerx, position[0], FPS / mps),
        #         lerp(self.rect.centery, position[1], FPS / mps)
        #     )


class Client:
    """The pong game client."""

    def __init__(self, screen_size: tuple[int, int] = (700, 700), fps: int = 60):
        """Initialize the client."""
        self.screen_size = screen_size
        self.fps = fps
        self.player_number = None
        self.updates: dict = {}
        self.paddles: dict[int, Paddle] = {}
        self.paddle_group = pygame.sprite.Group()

        self.start_event = threading.Event()
        self.stop_event = threading.Event()
        self.network_stop_event = threading.Event()

        self.mps = 0  # Messages per second
        self.average_mps = 0

        pygame.init()
        self.myfont = pygame.font.SysFont("monospace", 16)
        self.screen = pygame.display.set_mode(self.screen_size)

        self.main_menu = pygame_menu.Menu('', width=self.screen_size[0], height=self.screen_size[1], theme=menu_theme)
        self.ip_widget = self.main_menu.add.text_input("Host IP: ", default='zesty-zombies.pshome.me')
        self.main_menu.add.button("Connect", self.establish_connection, self.ip_widget)
        self.main_menu.add.button("Quit", self.exit)

        self.pause_menu = pygame_menu.Menu('', width=self.screen_size[0], height=self.screen_size[1], theme=menu_theme)
        self.pause_menu.add.button("Resume", lambda: self.pause_menu.disable())
        self.pause_menu.add.button("Disconnect", self.disconnect)
        self.pause_menu.add.button("Quit", self.exit)

    def main(self):
        self.stop_event.set()
        self.network_stop_event.set()
        self.main_menu.mainloop(self.screen)

    def cleanup(self):
        self.paddle_group = pygame.sprite.Group()
        self.paddles = {}
        self.player_number = None

    def exit(self):
        self.disconnect()
        pygame.quit()
        raise SystemExit

    def disconnect(self):
        self.stop_event.set()
        self.network_stop_event.set()
        self.pause_menu.disable()
        self.cleanup()

    def establish_connection(self, ip_widget):
        try:
            self.main_menu.remove_widget('msg')
        except (ValueError, AssertionError):  # AssertionError because pygame-menu uses a random assert
            pass
        ip = ip_widget.get_value()
        self.network_stop_event.set()
        self.network_thread = threading.Thread(target=lambda: asyncio.run(self.network_loop(ip)), daemon=True)
        self.network_stop_event.clear()
        self.network_thread.start()
        if self.start_event.wait(5):
            self.stop_event.clear()
            self.start_game()
        else:
            self.main_menu.add.label("Failed to connect to server", label_id='msg', font_color=(255, 0, 0))

    async def network_loop(self, ip: str):
        try:
            async with websockets.connect(f'ws://{ip}:8765') as websocket:
                await websocket.send(json.dumps({'type': 'init'}))
                while self.player_number is None:
                    message = json.loads(await websocket.recv())
                    if message['type'] == 'join':
                        self.player_number = message['data']['new']
                        for number in message['data']['ingame']:
                            self.paddles[number] = Paddle(number=number, local=False)
                self.start_event.set()
                while not self.network_stop_event.is_set():
                    data = {'type': 'paddle', 'data': self.paddles[self.player_number].rect.center}
                    await websocket.send(json.dumps(data))
                    message = json.loads(await websocket.recv())
                    self.mps += 1
                    if message['type'] == 'join':
                        self.paddles[message['data']['new']] = Paddle(number=message['data']['new'], local=False)
                        self.paddle_group.add(self.paddles[message['data']['new']])
                    elif message['type'] == 'leave':
                        self.paddle_group.remove(self.paddles[message['data']])
                    elif message['type'] == 'updates':
                        updates = message['data']
                        # Convert keys back to ints because yes
                        updates['players'] = {int(k): v for k, v in updates['players'].items()}
                        self.updates = updates
        except websockets.ConnectionClosed:
            self.stop_event.set()

    def get_score_text(self):
        text = ''
        for key in self.paddles:
            if key == self.player_number:
                text += "You: {}".format(self.paddles[key].score)
            else:
                text += 'Player {}: {}'.format(key, self.paddles[key].score)
        return text

    def start_game(self):
        """Run the game."""
        self.start_event.clear()
        ball = Ball()
        ball_group = pygame.sprite.Group(ball)
        local_paddle = Paddle(number=self.player_number)
        self.paddles[self.player_number] = local_paddle
        self.paddle_group.add(self.paddles.values())
        clock = pygame.time.Clock()
        counter = 0
        while True:
            if self.stop_event.is_set():
                break
            events = pygame.event.get()
            for event in events:
                if event.type == QUIT:
                    self.exit()
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.pause_menu.enable()
                        self.pause_menu.mainloop(self.screen)
            try:
                ball_group.update(self.updates['ball'], self.average_mps)
                self.paddle_group.update(self.updates['players'])
            except KeyError:  # Wouldn't be coding without more hacks eh?
                pass
            self.screen.fill((0, 0, 0))
            ball_group.draw(self.screen)
            self.paddle_group.draw(self.screen)
            scores_text = self.get_score_text()
            print(scores_text)
            scoretext = self.myfont.render(scores_text, 1, (255,255,255))
            self.screen.blit(scoretext, (5, 10))
            pygame.display.flip()  # Updates the display
            clock.tick(self.fps)
            counter += 1
            if counter == self.fps:
                self.average_mps = self.mps if self.average_mps == 0 else int(sum([self.mps, self.average_mps]) / 2)
                self.mps = 0
                counter = 0


SCREEN_WIDTH = 700
SCREEN_HEIGHT = 700

if __name__ == '__main__':
    client = Client()
    client.main()
