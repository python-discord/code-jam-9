import asyncio
import json
import os
import sys
import threading

# Disable stdout while importing Pygame to suppress hello message
s = sys.stdout
sys.stdout = open(os.devnull, 'w')
import pygame  # noqa: E402

sys.stdout = s

import websockets  # noqa: E402
from pygame.locals import QUIT  # noqa: E402

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 100
FPS = 60
ANGLE_MULTIPLIER = 75


def clamp(value, min_value, max_value):
    return min(max(value, min_value), max_value)


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

    def update(self, position):
        self.rect.center = position


class Client:
    def __init__(self):
        self.player_number = None
        self.updates = None
        self.paddles: dict[int, Paddle] = {}
        self.start_event = threading.Event()
        self.stop_event = threading.Event()
        self.paddle_group = pygame.sprite.Group()

    async def network_loop(self):
        try:
            async with websockets.connect('ws://zesty-zombies.pshome.me:8765') as websocket:
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

    async def main(self):
        self.network_thread = threading.Thread(target=lambda: asyncio.run(self.network_loop()), daemon=True)
        self.network_thread.start()
        self.start_event.wait()
        pygame.init()
        screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
        ball = Ball()
        ball_group = pygame.sprite.GroupSingle(ball)
        local_paddle = Paddle(number=self.player_number)
        self.paddles[self.player_number] = local_paddle
        self.paddle_group.add(self.paddles.values())
        clock = pygame.time.Clock()
        while True:
            if self.stop_event.is_set():
                raise SystemExit
            events = pygame.event.get()
            for event in events:
                if event.type == QUIT:
                    raise SystemExit
            pygame.event.pump()
            ball_group.update(self.updates['ball'])
            self.paddle_group.update(self.updates['players'])
            screen.fill((0, 0, 0))
            ball_group.draw(screen)
            self.paddle_group.draw(screen)
            pygame.display.flip()  # Updates the display
            clock.tick(FPS)


if __name__ == '__main__':
    client = Client()
    asyncio.run(client.main())
