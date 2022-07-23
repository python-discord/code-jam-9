import pygame as pg # I use pg since thats how I learned pygame
from pygame.locals import *
import math
import random
import sys

pg.init() # Inits pygame

SCREENWIDTH, SCREENHEIGHT = 500, 500
FPS = 30
ANGLEMULTIPLIER = 75

screen = pg.display.set_mode([SCREENWIDTH, SCREENHEIGHT]) # Creates a window with a specified size. The dimensions are arbritrary for now

def clamp(value, minvalue, maxvalue):
    return min(max(value, minvalue), maxvalue)

class Paddle(pg.sprite.Sprite): # Read pygame documentation on sprites and groups

    def __init__(self, direction = 1, size = (100, 100)): #dir is horizontal 0 or vertical 1 Maybe we can use an enum. Dir is obsolete for now
        super().__init__()
        self.direction = direction
        self.image = pg.Surface(size)
        self.image.fill((0, 0, 0))
        self.rect = self.image.get_rect()

    def update(self, events):
        mousepos =  pg.mouse.get_pos()[self.direction] # Mouse y value 
        if self.direction == 0:
            self.rect.centerx = clamp(mousepos, 0 + self.rect.width/2, SCREENWIDTH - self.rect.width/2)
        else:
            self.rect.centery = clamp(mousepos, 0 + self.rect.height/2, SCREENHEIGHT - self.rect.height/2)

class Ball(pg.sprite.Sprite):

    def __init__(self, speed = 10, size = (10, 10)):
        super().__init__()
        self.speed = speed
        self.horizontalspeed = 1 # 1 or -1 Backwards or forwards
        self.verticalspeed = 1 # Same as above
        self.angle = random.choice(range(90))
        self.image = pg.Surface(size)
        self.image.fill((0, 0, 0))
        self.rect = self.image.get_rect()
        self.x, self.y = SCREENWIDTH/2, SCREENHEIGHT/2 # Rect can't handle float values also can be used for syncing
    
    def update(self, events): 
        self.x += math.sin(self.angle*(math.pi/180)) * self.speed * self.horizontalspeed
        self.y -= math.cos(self.angle*(math.pi/180)) * self.speed * self.verticalspeed
        # Wall Collision
        if abs(self.x - (SCREENWIDTH/2)) > (SCREENWIDTH-self.rect.width)/2:
            self.x = clamp(self.x, self.rect.width/2, SCREENWIDTH - (self.rect.width/2))
            self.horizontalspeed *= -1
        if abs(self.y - (SCREENHEIGHT/2)) > (SCREENHEIGHT-self.rect.height)/2:
            self.y = clamp(self.y, self.rect.height/2, SCREENWIDTH - (self.rect.height/2))
            self.verticalspeed *= -1
        collide = pg.sprite.spritecollideany(self, paddles)
        if collide is not None:
            #print((math.degrees(math.atan2(-(collide.rect.y - self.rect.y), collide.rect.x - self.rect.x))-180)%360)
            collide = pg.sprite.spritecollideany(self, paddles)
            shifts = {
                "r": abs(self.rect.left - collide.rect.right),
                "l": abs(self.rect.right - collide.rect.left),
                "u": abs(self.rect.bottom - collide.rect.top),
                "d": abs(self.rect.top - collide.rect.bottom),
            }
            mshift = min(shifts.values())
            for k, v in shifts.items():
                if v == mshift:
                    move = {
                        "r": (mshift, 0),
                        "l": (-mshift, 0),
                        "u": (0, mshift),
                        "d": (0, -mshift),
                    }[k]
                    self.x += move[0]
                    self.y -= move[1]
                    self.x += move[0]
                    self.y -= move[1]
                    bounce = {
                        "r": (abs((collide.rect.centery - self.y)/(collide.rect.height)/2) * ANGLEMULTIPLIER, 1, -math.copysign(1, collide.rect.centery - self.y)),
                        "l": (abs((collide.rect.centery - self.y)/(collide.rect.height)/2) * ANGLEMULTIPLIER, -1, -math.copysign(1, collide.rect.centery - self.y)),
                        "u": (abs((collide.rect.centerx - self.x)/(collide.rect.width)/2) * ANGLEMULTIPLIER, math.copysign(1, collide.rect.centerx - self.x), 1),
                        "d": (abs((collide.rect.centerx - self.x)/(collide.rect.width)/2) * ANGLEMULTIPLIER, math.copysign(1, collide.rect.centerx - self.x), -1)
                    }[k]
                    self.angle = bounce[0]
                    self.horizontalspeed = bounce[1]
                    self.verticalspeed = bounce[2]
        self.rect.center = (self.x, self.y)

paddle = Paddle(1)
ball = Ball()
paddles = pg.sprite.Group(paddle)
balls = pg.sprite.Group(ball)
clock = pg.time.Clock()

while 1: # Basic update loop
    events = pg.event.get()
    for event in events: # Gets all current events 
        if event.type == QUIT: # Self explanatory
            pg.quit()
            sys.exit()
    screen.fill((255, 255, 255)) # White screen
    paddles.update(events)
    balls.update(events)
    paddles.draw(screen)
    balls.draw(screen)
    pg.display.flip() # Updates the display
    clock.tick(FPS)