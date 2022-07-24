import asyncio 
import time
from types import TracebackType
import websockets
import threading
import pygame as pg
from pygame.locals import *
import json
import sys

BALL_SIZE = (1,1)
PADDLE_LENGTH = None
PADDLE_WIDTH = None
SCREEN_WIDTH = None
SCREEN_HEIGHT = None, None
FPS = 60

def clamp(value, minvalue, maxvalue):
    return min(max(value, minvalue), maxvalue)

class Paddle(pg.sprite.Sprite): 

    def __init__(self, direction=1, client=None, pos=(0,0)): 
        super().__init__()
        self.direction = direction
        self.image = pg.Surface((PADDLE_LENGTH, PADDLE_WIDTH) if direction == 0 else (PADDLE_WIDTH, PADDLE_LENGTH))
        self.image.fill((0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.center = tuple(pos)
        self.client = client

    def update(self, events):
        if self.client is not None:
            mousepos = pg.mouse.get_pos()[self.direction] 
            if self.direction == 0:
                self.rect.centerx = clamp(mousepos, 0 + self.rect.width/2, SCREEN_WIDTH - self.rect.width/2)
            else:
                self.rect.centery = clamp(mousepos, 0 + self.rect.height/2, SCREEN_HEIGHT - self.rect.height/2)
            self.client.update_pos()

class Ball(pg.sprite.Sprite):

    def __init__(self, pos=(0,0)):
        super().__init__()
        self.image = pg.Surface(BALL_SIZE)
        self.image.fill((0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.center = tuple(pos)

class Client:

    def __init__(self):
        self.client = None
        self.players = []
        self.ball = Ball()
        self.player = None
        self.player_number = None
        self.network_loop = None
        self.info_wait = threading.Condition()
        self.network_thread = threading.Thread(target=lambda:asyncio.run(self.connect()))
        self.network_thread.start()
        self.info_wait.acquire()
        while SCREEN_WIDTH == None:
            self.info_wait.wait()
        self.info_wait.release()

    async def connect(self):
        self.info_wait.acquire()
        async with websockets.connect("ws://localhost:8765") as client:
            self.client = client
            #self.network_loop.run_forever()
            while 1:
                self.process(json.loads(await self.client.recv()))


    def process(self, message):
        if message["type"] == "info":
            message = message["data"]
            global SCREEN_WIDTH, SCREEN_HEIGHT, PADDLE_WIDTH, PADDLE_LENGTH
            SCREEN_WIDTH = message["screen_width"]
            SCREEN_HEIGHT = message["screen_height"]
            PADDLE_WIDTH = message["paddle_width"]
            PADDLE_LENGTH = message["paddle_length"]
            self.player_number = message["paddle_num"]
            self.info_wait.notify_all()
            self.info_wait.release()

        elif message["type"] == "broadcast":
            message = message["data"]
            if not len(message["players"]) == len(self.players):
                self.players = []
                for player in message["players"]:
                    if not player["player_number"] == self.player_number:
                        self.players.append(Paddle(pos=player["position"]))
                    elif self.player == None:
                        self.player = Paddle(int(self.player_number > 1), client=self, pos=player["position"])
            else:
                for player in message["players"]:
                    if not player["player_number"] == self.player_number:
                        self.player.rect.center = player["position"]
            self.ball.rect.center = message["ball"]

    def update_pos(self):
        self.network_loop.call_soon_threadsafe(self.client.send(json.dumps({"type":"paddle", "data": self.player.rect.center})))

pg.init()
pg.event.set_allowed(QUIT)
client = Client()
screen = pg.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
clock = pg.time.Clock()

while 1:
    events = pg.event.get()
    for event in events:  # Gets all current events
        if event.type == QUIT:  # Self explanatory
            pg.quit()
            sys.exit()
    try:
        client.player.update(events)
    except:
        pass
    screen.fill((255, 255, 255))
    screen.blit(client.ball.image, client.ball.rect)
    screen.blit(client.player.image, client.player.rect)
    for paddle in client.players:
        screen.blit(paddle.image, paddle.rect)
    pg.display.flip()
    clock.tick(FPS)