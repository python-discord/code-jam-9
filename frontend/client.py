import asyncio
import json
import os
import sys

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
            mousepos = pygame.mouse.get_pos()[self.direction]  # Mouse y value
            if self.direction == 0:
                self.rect.centerx = clamp(mousepos, self.rect.width / 2, SCREEN_WIDTH - self.rect.width / 2)
            else:
                self.rect.centery = clamp(mousepos, self.rect.height / 2, SCREEN_HEIGHT - self.rect.height / 2)
        else:
            self.rect.center = players[self.number]['position']


class Ball(pygame.sprite.Sprite):
    def __init__(self, speed=10, size=(10, 10)):
        super().__init__()
        self.image = pygame.Surface(size)
        self.image.fill((255, 255, 255))
        self.rect = self.image.get_rect()

    def update(self, position):
        self.rect.center = position


class Client:
    def __init__(self):
        self.websocket = None
        self.player_number = None

    async def main(self):
        self.websocket = await websockets.connect('ws://localhost:8765')
        await self.websocket.send(json.dumps({'type': 'init'}))
        player_number = None
        while player_number is None:
            message = json.loads(await self.websocket.recv())
            if message['type'] == 'join':
                player_number = message['data']
        pygame.init()
        screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
        ball = Ball()
        ball_group = pygame.sprite.GroupSingle(ball)
        local_paddle = Paddle(number=player_number)
        paddle_group = pygame.sprite.Group(local_paddle)
        clock = pygame.time.Clock()

        try:
            while True:
                await self.websocket.send(json.dumps({'type': 'paddle', 'data': local_paddle.rect.center}))
                message = json.loads(await self.websocket.recv())
                if message['type'] == 'join':
                    paddle_group.add(Paddle(number=message['data'], local=False))
                elif message['type'] == 'leave':
                    p = [p for p in paddle_group if p.number == message['data']][0]
                    paddle_group.remove(p)
                elif message['type'] == 'updates':
                    updates = message['data']
                    # Convert keys back to ints because yes
                    updates['players'] = {int(k): v for k, v in updates['players'].items()}
                    events = pygame.event.get()
                    for event in events:
                        if event.type == QUIT:
                            pygame.quit()
                            raise SystemExit
                    pygame.event.pump()

                    ball_group.update(updates['ball'])
                    paddle_group.update(updates['players'])

                screen.fill((0, 0, 0))
                ball_group.draw(screen)
                paddle_group.draw(screen)
                pygame.display.flip()  # Updates the display
                clock.tick(FPS)
        finally:
            await self.websocket.close()


if __name__ == '__main__':
    client = Client()
    asyncio.run(client.main())
