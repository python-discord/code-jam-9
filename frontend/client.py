"""The client code."""

import asyncio
import json
import threading

import arcade
import websockets

# menu_theme = pygame_menu.Theme(
#     background_color=(0, 0, 0, 0),
#     widget_font=pygame_menu.font.FONT_MUNRO,
#     title_bar_style=pygame_menu.widgets.MENUBAR_STYLE_NONE,
# )


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Restrict the provided value to be between a minimum and maximum."""
    return min(max(value, min_value), max_value)


def lerp(value: float, new_value: float, multiplier: float) -> float:
    """Do linear interpolation on the provided value."""
    return value + (multiplier * (new_value - value))


class Paddle(arcade.Sprite):
    """The paddle sprite."""

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
        self.color = arcade.color.WHITE
        if self.number == 0:
            self.center_x = 30
        elif self.number == 1:
            self.center_x = SCREEN_WIDTH - 30
        elif self.number == 2:
            self.center_y = 30
        elif self.number == 3:
            self.center_y = SCREEN_HEIGHT - 30

    def update(self, position: tuple[int, int]):
        """Update the paddle location.

        Args:
            position (tuple): The position of the paddle.
        """
        if self.local:
            mouse_pos = position[self.direction]
            if self.direction == 0:
                self.center_x = clamp(mouse_pos, self.width / 2, SCREEN_WIDTH - self.width / 2)
            else:
                self.center_y = clamp(mouse_pos, self.height / 2, SCREEN_HEIGHT - self.height / 2)
        else:
            self.center_x, self.center_y = position

    def draw(self):
        arcade.draw_rectangle_filled(self.center_x, self.center_y, self.width, self.height, self.color)


class Ball(arcade.Sprite):
    """The ball sprite."""

    def __init__(self, width: int = 10, height: int = 10):
        """Initialize a ball sprite.

        Args:
            width (int, optional): The width of the ball sprite. Defaults to 10.
            height (int, optional): The height of the ball sprite. Defaults to 10.
        """
        super().__init__()
        self.width = width
        self.height = height
        self.color = arcade.color.WHITE

    def update(self, position: tuple[int, int]):
        """Update the ball location.

        Args:
            position (tuple): The XY coordinates of the ball.
        """
        self.center_x, self.center_y = position

    def draw(self):
        arcade.draw_rectangle_filled(self.center_x, self.center_y, self.width, self.height, self.color)


class Client(arcade.Window):
    """The pong game client."""

    def __init__(self, width: int = 700, height: int = 700, title: str = "Pong"):
        """Initialize the client."""
        super().__init__(width, height, title)
        self.set_mouse_visible(False)
        self.player_number = None
        self.updates: dict = {}
        self.paddles: dict[int, Paddle] = {}
        self.local_paddle: Paddle = None
        self.ball: Ball = None

        self.start_event = threading.Event()
        self.stop_event = threading.Event()
        self.network_stop_event = threading.Event()

        # self.manager = arcade.gui.UIManager()
        # self.manager.enable()
        # arcade.set_background_color(arcade.color.BLACK)
        # self.v_box = arcade.gui.UIBoxLayout()

        # start_button = arcade.gui.UIFlatButton(text="Start Game", width=200)
        # start_button.on_click = self.main
        # self.v_box.add(start_button.with_space_around(bottom=20))

        # settings_button = arcade.gui.UIFlatButton(text="Settings", width=200)
        # self.v_box.add(settings_button.with_space_around(bottom=20))

        # self.manager.add(
        #     arcade.gui.UIAnchorWidget(
        #         anchor_x="center_x",
        #         anchor_y="center_y",
        #         child=self.v_box)
        # )

        # self.screen = pygame.display.set_mode([width, height])

        # self.main_menu = pygame_menu.Menu('', width=width, height=height, theme=menu_theme)
        # self.ip_widget = self.main_menu.add.text_input("Host IP: ", default='zesty-zombies.pshome.me')
        # self.main_menu.add.button("Connect", self.establish_connection, self.ip_widget)
        # self.main_menu.add.button("Quit", self.exit)

        # self.pause_menu = pygame_menu.Menu('', width=width, height=height, theme=menu_theme)
        # self.pause_menu.add.button("Resume", lambda: self.pause_menu.disable())
        # self.pause_menu.add.button("Disconnect", self.disconnect)
        # self.pause_menu.add.button("Quit", self.exit)

    def exit(self):
        self.disconnect()
        arcade.exit()
        raise SystemExit

    def cleanup(self):
        self.paddles = {}
        self.player_number = None

    def disconnect(self):
        self.network_stop_event.set()
        # self.pause_menu.disable()
        self.cleanup()

    def connect(self, ip):
        # try:
        #     self.main_menu.remove_widget('msg')
        # except (ValueError, AssertionError):  # AssertionError because pygame-menu uses a random assert
        #     pass
        # ip = ip_widget.get_value()
        self.disconnect()
        self.network_thread = threading.Thread(target=lambda: asyncio.run(self.network_loop(ip)), daemon=True)
        self.network_stop_event.clear()
        self.network_thread.start()
        if self.start_event.wait(5):
            self.start_event.clear()
            self.stop_event.clear()
        else:
            # self.main_menu.add.label("Failed to connect to server", label_id='msg', font_color=(255, 0, 0))
            print("Failed to connect to server")

    async def network_loop(self, ip: str):
        try:
            async with websockets.connect(f'ws://{ip}:8765') as websocket:
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
                        )
                    }
                    await websocket.send(json.dumps(data))
                    message = json.loads(await websocket.recv())
                    if message['type'] == 'join':
                        self.paddles[message['data']['new']] = Paddle(number=message['data']['new'], local=False)
                    elif message['type'] == 'leave':
                        del self.paddles[message['data']]
                    elif message['type'] == 'updates':
                        updates = message['data']
                        # Convert keys back to ints because yes
                        updates['players'] = {int(k): v for k, v in updates['players'].items()}
                        self.updates = updates
        except websockets.ConnectionClosed:
            self.stop_event.set()

    def on_update(self, delta_time: float):
        if not self.updates:
            return
        if self.stop_event.is_set():
            self.exit()
        self.clear()
        self.local_paddle.draw()
        self.ball.update(self.updates['ball'])
        self.ball.draw()
        for number, paddle in self.paddles.items():
            try:
                paddle.update(position=self.updates['players'][number]['position'])
                paddle.draw()
            except KeyError:  # When updates variable hasn't been updated yet
                pass

    def on_mouse_motion(self, x, y, dx, dy):
        self.local_paddle.update(position=(x, y))

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            self.exit()


SCREEN_WIDTH = 700
SCREEN_HEIGHT = 700

if __name__ == '__main__':
    client = Client()
    client.connect('localhost')
    client.run()
