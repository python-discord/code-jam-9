"""The client code."""

import asyncio
import json
import math
import os
import random
import threading

import arcade
import arcade.color
import arcade.gui
import arcade.key
import websockets
from arcade.experimental.texture_render_target import RenderTargetTexture


class ChromaticAberration(RenderTargetTexture):
    def __init__(self, width, height):
        super().__init__(width, height)
        with open(os.path.join(ASSETS_DIR, 'shaders', 'fragment.glsl')) as file:
            fragment_shader = file.read()
        with open(os.path.join(ASSETS_DIR, 'shaders', 'vertex.glsl')) as file:
            vertex_shader = file.read()
        self.program = self.ctx.program(fragment_shader=fragment_shader, vertex_shader=vertex_shader)
        self.program["resolution"] = (width, height)

    def use(self):
        self._fbo.use()

    def draw(self):
        self.texture.use(0)
        self._quad_fs.render(self.program)


class Paddle(arcade.Sprite):
    """The paddle sprite."""

    color = arcade.color.WHITE

    def __init__(self, width: int = 10, height: int = 100, number: int = 0, direction: int = 1, local: bool = True):
        """Initialize a paddle sprite.

        Args:
            width (int, optional): The width of the paddle sprite. Defaults to 10.
            height (int, optional): The height of the paddle sprite. Defaults to 100.
            number (int, optional): The paddle number. Defaults to 0.
            direction (int, optional): Determines whether the paddle is vertical or horizontal. Defaults to 1.
            local (bool, optional): Set to True if the paddle movement is controlled by the client. Defaults to True.
        """
        super().__init__()
        self.width = width
        self.height = height
        self.number = number
        self.direction = direction
        self.local = local
        if self.number > 1:
            self.direction = 0
        if self.direction == 0:
            self.width, self.height = self.height, self.width
        if self.number == 0:
            self.center_x = 30
        elif self.number == 1:
            self.center_x = SCREEN_WIDTH - 30
        elif self.number == 2:
            self.center_y = 30
        elif self.number == 3:
            self.center_y = SCREEN_HEIGHT - 30
        self.inverted = False

    def clamp(self, value: float, min_value: float, max_value: float) -> float:
        """Restrict the provided value to be between a minimum and maximum."""
        return min(max(value, min_value), max_value)

    def update(self, position: tuple[int, int]):
        """Update the paddle location.

        Args:
            position (tuple): The position of the paddle.
        """
        if self.local:
            mouse_pos = position[self.direction]
            if self.direction == 0:
                if self.inverted:
                    self.center_x = abs(
                        SCREEN_WIDTH - self.clamp(mouse_pos, self.width / 2, SCREEN_WIDTH - self.width / 2)
                    )
                else:
                    self.center_x = self.clamp(mouse_pos, self.width / 2, SCREEN_WIDTH - self.width / 2)
            else:
                if self.inverted:
                    self.center_y = abs(
                        SCREEN_HEIGHT - self.clamp(mouse_pos, self.height / 2, SCREEN_HEIGHT - self.height / 2)
                    )
                else:
                    self.center_y = self.clamp(mouse_pos, self.height / 2, SCREEN_HEIGHT - self.height / 2)
        else:
            self.center_x, self.center_y = position

    def draw(self):
        arcade.draw_rectangle_filled(self.center_x, self.center_y, self.width, self.height, self.color)


class Ball(arcade.Sprite):
    """The ball sprite."""

    def __init__(self):
        """Initialize a ball sprite.

        Args:
            width (int, optional): The width of the ball sprite. Defaults to 10.
            height (int, optional): The height of the ball sprite. Defaults to 10.
        """
        super().__init__()
        self.textures: list[arcade.Texture] = []
        self.textures.append(arcade.load_texture(os.path.join(ASSETS_DIR, 'images', 'bug.png')))
        self.textures.append(arcade.load_texture(os.path.join(ASSETS_DIR, 'images', 'dvd.png')))
        self.alpha = 255
        self.ball_texture = 0

    def update(self, position: tuple[int, int]):
        """Update the ball location.

        Args:
            position (tuple): The XY coordinates of the ball.
        """
        self.center_x, self.center_y = position

    def draw(self):
        self.textures[self.ball_texture].draw_scaled(self.center_x, self.center_y, scale=1.75, alpha=self.alpha)


class Brick(arcade.Sprite):
    def __init__(self, width: int = 10, height: int = 10):
        """The Brick sprite."""

        super().__init__()
        self.width = width
        self.height = height
        self.color = arcade.color.WHITE

    def update(self, position: tuple[int, int]):
        self.center_x, self.center_y = position

    def draw(self):
        arcade.draw_rectangle_filled(self.center_x, self.center_y, self.width, self.height, self.color)


class Powerup:
    def __init__(self, client):
        pass

    def update(self):
        pass

    def end(self):
        pass

    @staticmethod
    def to_string():
        return 'a powerup'


class InvisiblePaddlePowerup(Powerup):
    def __init__(self, client):
        self.timer = 0
        self.client = client

    def update(self):
        self.timer += 0.01
        Paddle.color = (*arcade.color.WHITE, int((abs(math.sin(self.timer))) * 255 * 0.05))

    def end(self):
        if len([powerup for powerup in client.powerups if isinstance(powerup, InvisiblePaddlePowerup)]) <= 1:
            Paddle.color = arcade.color.WHITE

    @staticmethod
    def to_string():
        return 'an invisible paddle powerup'


class InvisibleBallPowerup(Powerup):
    def __init__(self, client):
        self.timer = 0
        self.client = client

    def update(self):
        self.timer += 0.01
        self.client.ball.alpha = int((abs(math.sin(self.timer))) * 255 * 0.1)

    def end(self):
        if len([powerup for powerup in client.powerups if isinstance(powerup, InvisibleBallPowerup)]) <= 1:
            self.client.ball.alpha = 255

    @staticmethod
    def to_string():
        return 'an invisible ball powerup'


class InvertedPaddlePowerup(Powerup):
    def __init__(self, client):
        self.timer = 0
        self.client = client
        self.client.local_paddle.inverted = True

    def end(self):
        if len([powerup for powerup in client.powerups if isinstance(powerup, InvertedPaddlePowerup)]) <= 1:
            self.client.local_paddle.inverted = False

    @staticmethod
    def to_string():
        return 'an inverted paddle movement powerup'


class GameView(arcade.View):
    """The game view."""

    def __init__(self, client: "Client"):
        super().__init__()
        self.client = client
        self.shader = ChromaticAberration(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.timer = 0
        self.powerup_message_timer = -1

    def on_show_view(self):
        self.client.set_mouse_visible(False)

    def on_hide_view(self):
        self.client.set_mouse_visible(True)

    def on_update(self, delta_time: float):
        if random.randint(1, 30) > 2:
            self.timer += delta_time
            self.shader.program["time"] = self.timer
        if self.client.powerup_message_data is not None:
            if self.powerup_message_timer == -1:
                self.powerup_message_timer = 3 * 60
            self.powerup_message_timer -= 1
            if self.powerup_message_timer == 0:
                self.powerup_message_timer = -1
                self.client.powerup_message_data = None
        if not self.client.updates:
            return
        if self.client.stop_event.is_set():
            self.client.exit()
        self.client.ball.update(self.client.updates['ball'])
        for number, paddle in self.client.paddles.items():
            try:
                paddle.update(position=self.client.updates['players'][number]['position'])
            except KeyError:  # When updates variable hasn't been updated yet
                pass
        for index, brick in enumerate(self.client.bricks):
            try:
                brick.update(position=self.client.updates['bricks'][index]["position"])
            except IndexError:  # Wouldn't be coding without a few hacks ¯\_(ツ)_/¯
                pass
        for powerup in self.client.powerups:
            powerup.update()
        self.shader.program["glitch"] = len(self.client.powerups) > 0

    def on_draw(self):
        self.clear()
        self.shader.clear()
        self.shader.use()
        self.client.local_paddle.draw()
        self.client.ball.draw()
        for paddle in self.client.paddles.values():
            if paddle.number == self.client.player_number:  # Remove after updating server deployment
                continue
            paddle.draw()
        for brick in self.client.bricks:
            brick.draw()
        arcade.draw_text(
            self.client.scores_text,
            10,
            10,
            arcade.color.WHITE,
            18,
        )
        if self.client.powerup_message_data is not None:
            if self.client.powerup_message_data[0] == self.client.player_number:
                player = "You"
            else:
                player = f"Player {self.client.powerup_message_data[0] + 1}"
            arcade.draw_text(
                # I didn't write this globals() stuff but if it works I'd better not touch it  -- LemonPi314
                f"{player} used {globals()[self.client.powerup_message_data[1]].to_string()}",
                100,
                600,
                (*arcade.color.WHITE, 255 * int((3 * 60) / self.powerup_message_timer)),
                18,
            )
        self.window.use()
        self.shader.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        if self.client.local_paddle:
            self.client.local_paddle.update(position=(x, y))

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            self.client.pause()


class MainMenuView(arcade.View):
    """The main menu view."""

    def __init__(self, client: "Client"):
        super().__init__()
        self.client = client

        self.manager = arcade.gui.UIManager()
        v_box = arcade.gui.UIBoxLayout()

        ip_title = arcade.gui.UILabel(text="SERVER IP:", font_size=20, font_color=arcade.color.WHITE)
        v_box.add(ip_title)

        ip_input = arcade.gui.UIInputText(text='localhost', width=200, text_color=arcade.color.WHITE)
        v_box.add(ip_input)

        connect_button = arcade.gui.UIFlatButton(text="CONNECT", width=200)
        connect_button.on_click = lambda event: self.client.connect(ip_input.text)
        v_box.add(connect_button.with_space_around(bottom=20))

        exit_button = arcade.gui.UIFlatButton(text="EXIT", width=200)
        exit_button.on_click = lambda event: self.client.exit()
        v_box.add(exit_button.with_space_around(bottom=20))

        self.menu_message = arcade.gui.UILabel(
            text='', width=400, height=20, align='center', text_color=arcade.color.WHITE
        )
        v_box.add(self.menu_message)

        self.manager.add(arcade.gui.UIAnchorWidget(anchor_x="center_x", anchor_y="center_y", child=v_box))

    def on_show_view(self):
        self.manager.enable()

    def on_hide_view(self):
        self.manager.disable()

    def on_draw(self):
        self.clear()
        self.manager.draw()


class PauseMenuView(arcade.View):
    """The pause menu view."""

    def __init__(self, client: "Client"):
        super().__init__()
        self.client = client

        self.manager = arcade.gui.UIManager()
        v_box = arcade.gui.UIBoxLayout()

        resume_button = arcade.gui.UIFlatButton(text="RESUME", width=200)
        resume_button.on_click = lambda event: self.client.resume()
        v_box.add(resume_button.with_space_around(bottom=20))

        disconnect_button = arcade.gui.UIFlatButton(text="DISCONNECT", width=200)
        disconnect_button.on_click = lambda event: self.client.disconnect()
        v_box.add(disconnect_button.with_space_around(bottom=20))

        exit_button = arcade.gui.UIFlatButton(text="EXIT", width=200)
        exit_button.on_click = lambda event: self.client.exit()
        v_box.add(exit_button.with_space_around(bottom=20))

        self.manager.add(arcade.gui.UIAnchorWidget(anchor_x="center_x", anchor_y="center_y", child=v_box))

    def on_show_view(self):
        self.manager.enable()

    def on_hide_view(self):
        self.manager.disable()

    def on_draw(self):
        self.clear()
        self.manager.draw()


class Client(arcade.Window):
    """The pong game client."""

    def __init__(self, width: int = 700, height: int = 700, title: str = "Pong"):
        super().__init__(width, height, title)
        self.player_number = None
        self.updates: dict = {}
        self.paddles: dict[int, Paddle] = {}
        self.local_paddle: Paddle = None  # type: ignore
        self.ball: Ball = None  # type: ignore
        self.bricks: list[Brick] = []
        self.scores_text = "Get ready!"
        self.powerups: list[Powerup] = []
        self.powerup_message_data = None

        self.network_thread = None
        self.start_event = threading.Event()
        self.stop_event = threading.Event()
        self.network_stop_event = threading.Event()

        self.game_view = GameView(self)
        self.main_menu_view = MainMenuView(self)
        self.pause_menu_view = PauseMenuView(self)

        arcade.set_background_color(arcade.color.BLACK)
        self.show_view(self.main_menu_view)

    def pause(self):
        self.show_view(self.pause_menu_view)

    def resume(self):
        self.show_view(self.game_view)

    def exit(self):
        self.disconnect()
        arcade.exit()

    def cleanup(self):
        self.paddles = {}
        self.player_number = None
        self.show_view(self.main_menu_view)

    def disconnect(self):
        self.network_stop_event.set()
        if self.network_thread:
            self.network_thread.join()
        self.cleanup()

    def connect(self, ip: str):
        self.disconnect()
        self.network_thread = threading.Thread(target=lambda: asyncio.run(self.network_loop(ip)), daemon=True)
        self.network_stop_event.clear()
        self.network_thread.start()
        if self.start_event.wait(5):
            self.start_event.clear()
            self.stop_event.clear()
            self.show_view(self.game_view)
        else:
            self.main_menu_view.menu_message.text = "FAILED TO CONNECT TO SERVER"

    def get_score_text(self) -> str:
        text = ''
        for key in self.updates['players']:
            if self.updates['players'][key]['player_number'] == self.player_number:
                text += f"You: {self.updates['players'][key]['score']} "
            else:
                text += (
                    f"Player {self.updates['players'][key]['player_number'] + 1}: "
                    f"{self.updates['players'][key]['score']} "
                )
        return text

    async def network_loop(self, ip: str):
        try:
            async with websockets.connect(f'ws://{ip}:8765') as websocket:  # type: ignore
                await websocket.send(json.dumps({'type': 'init'}))
                while self.player_number is None:
                    message = json.loads(await websocket.recv())
                    if message['type'] == 'join':
                        self.player_number = message['data']['new']
                        self.local_paddle = Paddle(number=self.player_number)
                        self.ball = Ball()
                        for number in message['data']['ingame']:
                            self.paddles[number] = Paddle(number=number, local=False)
                self.start_event.set()
                while not self.network_stop_event.is_set():
                    data = {
                        'type': 'paddle',
                        'data': (
                            self.local_paddle.center_x,
                            self.local_paddle.center_y,
                        ),
                    }
                    await websocket.send(json.dumps(data))
                    message = json.loads(await websocket.recv())
                    if message['type'] == 'join':
                        self.paddles[message['data']['new']] = Paddle(number=message['data']['new'], local=False)
                    elif message['type'] == 'leave':
                        del self.paddles[message['data']]
                    elif message['type'] == 'new_powerup':
                        self.powerup_message_data = (message['data']['user'], message['data']['type'])
                    elif message['type'] == 'updates':
                        updates = message['data']
                        # Convert keys back to ints because yes
                        updates['players'] = {int(k): v for k, v in updates['players'].items()}
                        self.updates = updates
                        self.ball.ball_texture = self.updates['ball_texture']
                        self.scores_text = self.get_score_text()
                        if not len(updates['bricks']) == len(self.bricks):
                            self.bricks = []
                            for brick in updates['bricks']:
                                self.bricks.append(Brick(*brick['size']))
                        if not len(updates['powerups']) == len(self.powerups):
                            for powerup in self.powerups:
                                powerup.end()
                            self.powerups = []
                            for powerup in updates['powerups']:
                                if not powerup["user"] == self.local_paddle.number:
                                    self.powerups.append(globals()[powerup["type"]](self))
        except websockets.ConnectionClosed:  # type: ignore
            self.stop_event.set()


SCREEN_WIDTH = 700
SCREEN_HEIGHT = 700
ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')

if __name__ == '__main__':
    client = Client()
    client.run()
