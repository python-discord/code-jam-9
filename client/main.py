import json
from typing import Optional

from available_commands import AvailableCommands
from console import Console
from entities import Entities
from map import Map
from websocket_app import WebsocketApp


class GameInterface(WebsocketApp):
    """Simple textual app.

    Just placeholders to be replaced once we get the client going.
    """

    name: Optional[str] = None

    async def on_mount(self) -> None:
        grid = await self.view.dock_grid(edge="left", name="left")

        grid.add_column(fraction=1, name="left")
        grid.add_column(fraction=2, name="center")
        grid.add_column(fraction=1, name="right")

        grid.add_row(fraction=1, name="top", min_size=2)
        grid.add_row(fraction=1, name="middle")
        grid.add_row(fraction=1, name="bottom")

        grid.add_areas(
            map_area="left-start|center-end,top-start|middle-end",
            entities_area="right,top-start|middle-end",
            events_area="left-start|center-end,bottom",
            available_commands_area="right,bottom",
        )

        self.console_widget = Console(main_app=self, name="Console")
        self.available_commands_widget = AvailableCommands(
            main_app=self, name="Available Commands"
        )

        grid.place(
            map_area=Map(),
            entities_area=Entities(),
            events_area=self.console_widget,
            available_commands_area=self.available_commands_widget,
        )

    async def handle_messages(self):
        """Allows receiving messages from a websocket and handling them."""
        while self.websocket.open:
            message = json.loads(await self.websocket.recv())
            match message["type"]:
                case "chat":
                    self.console_widget.out.add_log(
                        f"{message['player_name']}: {message['chat_message']}"
                    )
                    self.console_widget.refresh()
                case "registration_successful":
                    self.name = message["player"]["name"]
                    self.console_widget.name = self.name
                    self.console_widget.out.add_log(
                        f"Correctly registered as {self.name}"
                    )
                    self.console_widget.refresh()


try:
    GameInterface.run(log="textual.log")
except ConnectionRefusedError:
    print("Make sure there's a server running before trying to run the client.")
