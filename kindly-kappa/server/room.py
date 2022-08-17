from datetime import datetime
from uuid import UUID

from server.client import Client
from server.events import Position, ReplaceData, Replacement
from server.modifiers import FOUR_SPACES, Modifiers


class Room:
    """A room handled by the connection manager."""

    def __init__(self, owner_id: UUID, clients: set[Client], difficulty: int) -> None:
        """Initializes the room.

        Args:
            owner_id: The id of the owner of the room.
            clients: The connected clients.
            difficulty: The difficulty of the room.
        """
        self.owner_id = owner_id
        self.clients = clients
        self.difficulty = difficulty
        self.code = ""
        self.cursors: dict[UUID, Position] = {}
        self.epoch = datetime.now()

    def update_code(self, replace_data: ReplaceData) -> None:
        """Updates the code.

        Args:
            replace_data: A list of changes to make to the code.
        """
        current_code = self.code

        # This checks if there was a de-indent (E.g after a function or class)
        # and adds the newline since it doesn't get passed from the frontend
        if len(replace_data.code) == 2:
            new_value = f"\n{FOUR_SPACES}"
            repalcement_value = Replacement(**replace_data.code[1])
            repalcement_value["value"] = new_value
            replace_data.code[1] |= repalcement_value

        for replacement in replace_data.code:
            from_index = replacement["from"]
            to_index = replacement["to"]
            new_value = replacement["value"]

            updated_code = current_code[:from_index] + new_value + current_code[to_index:]
            self.code = updated_code

    def set_code(self, updated_code: str) -> None:
        """Sets the code.

        Args:
            updated_code: A string containing the new code.
        """
        self.code = updated_code

    def introduce_bugs(self) -> None:
        """Introduces bugs based on the current code."""
        if self.code.strip() == "":
            return

        modifier = Modifiers(self.code, self.difficulty)

        for code_change in modifier.output.code:
            self.update_code(ReplaceData(code=[code_change]))
