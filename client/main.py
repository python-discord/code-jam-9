from console import Console
from map import Map
from textual.app import App
from textual.widgets import Placeholder


class GameInterface(App):
    """Simple textual app.

    Just placeholders to be replaced once we get the client going.
    """

    async def on_mount(self) -> None:
        # map_area = Map()
        # entities_area = Placeholder(name="Entities in the map")
        # console_area = Console()
        # available_commands_area = Placeholder(name="Available Commands")

        # await self.view.dock(map_area, edge="left")
        # await self.view.dock(console_area, edge="left")
        # await self.view.dock(entities_area, edge="right")
        # await self.view.dock(available_commands_area, edge="right")

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

        grid.place(
            map_area=Map(),
            entities_area=Placeholder(name="Entities in the map"),
            events_area=Console(),
            available_commands_area=Placeholder(name="Available Commands"),
        )


GameInterface.run(log="textual.log")
