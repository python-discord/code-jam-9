import asyncio
import json
import os
import sys
import threading

# Disable stdout while importing Pygame to suppress hello message
s = sys.stdout
sys.stdout = open(os.devnull, 'w')
import pygame  # noqa: E402
import pygame_menu  # noqa: E402

sys.stdout = s

import websockets  # noqa: E402
from pygame.locals import QUIT  # noqa: E402

SCREEN_WIDTH = 700
SCREEN_HEIGHT = 700
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 100
FPS = 60
ANGLE_MULTIPLIER = 75


def clamp(value, min_value, max_value):
    return min(max(value, min_value), max_value)


def lerp(value, new_value, multiplier):
    return value + (multiplier * (new_value - value))


class Paddle(pygame.sprite.Sprite):  # Read pygame documentation on sprites and groups
    def __init__(self, direction=1, size=(PADDLE_WIDTH, PADDLE_HEIGHT), number=0, local=True):
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
    def __init__(self, size=(10, 10)):
        super().__init__()
        self.image = pygame.Surface(size)
        self.image.fill((255, 255, 255))
        self.rect = self.image.get_rect()

    def update(self, position, mps):
        self.rect.center = position
        # if mps == 0:
        #     self.rect.center = position
        # else:
        #     self.rect.center = (
        #         lerp(self.rect.centerx, position[0], FPS / mps),
        #         lerp(self.rect.centery, position[1], FPS / mps)
        #     )


class Client:
    def __init__(self):
        self.player_number = None
        self.updates = None
        self.paddles: dict[int, Paddle] = {}
        self.start_event = threading.Event()
        self.stop_event = threading.Event()
        self.paddle_group = pygame.sprite.Group()
        self.mps = 0  # Messages per second
        self.average_mps = 0

    async def network_loop(self, ip):
        try:
            async with websockets.connect('ws://'+ip+':8765') as websocket:
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

    def start_game(self, screen):
        ball = Ball()
        ball_group = pygame.sprite.GroupSingle(ball)
        local_paddle = Paddle(number=self.player_number)
        self.paddles[self.player_number] = local_paddle
        self.paddle_group.add(self.paddles.values())
        clock = pygame.time.Clock()
        counter = 0
        while True:
            if self.stop_event.is_set():
                raise SystemExit
            events = pygame.event.get()
            for event in events:
                if event.type == QUIT:
                    raise SystemExit
            pygame.event.pump()
            ball_group.update(self.updates['ball'], self.average_mps)
            self.paddle_group.update(self.updates['players'])
            screen.fill((0, 0, 0))
            ball_group.draw(screen)
            self.paddle_group.draw(screen)
            pygame.display.flip()  # Updates the display
            clock.tick(FPS)
            counter += 1
            if counter == FPS:
                self.average_mps = self.mps if self.average_mps == 0 else int(sum([self.mps, self.average_mps])/2)
                self.mps = 0
                counter = 0

    def establish_connection(self, ip, screen):
        self.network_thread = threading.Thread(target=lambda: asyncio.run(self.network_loop(ip)), daemon=True)
        self.network_thread.start()
        self.start_event.wait()
        self.main_menu.add.button('Play', self.start_game, screen)
        self.main_menu.add.button('Quit', pygame_menu.events.EXIT)

    def menu(self, screen):
        self.main_menu = pygame_menu.Menu('main menu', 400, 300, theme=pygame_menu.themes.THEME_BLUE)
        ip = self.main_menu.add.text_input('Host Ip :', default='zesty-zombies.pshome.me')
        self.main_menu.add.button('Connect', self.establish_connection, ip.get_value(), screen)
        self.main_menu.mainloop(screen)

    async def main(self):
        pygame.init()
        screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
        self.menu(screen)


if __name__ == '__main__':
    client = Client()
    asyncio.run(client.main())
