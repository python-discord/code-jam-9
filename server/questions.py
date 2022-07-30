import json
import random


class Questions:
    """Container class for game questions."""

    def __init__(self) -> None:
        with open("./server/questions.json", "r") as f:
            questions = json.load(f)
        self.questions = [random.choice(questions["questions"]) for i in range(5)]
        self.index = 0

    def next(self) -> dict:
        """
        Returns the next question required for the game.

        If there are no more questions, this function will return an empty dict.
        """
        try:
            self.index += 1
            return self.questions[self.index - 1]
        except IndexError:
            return {}
