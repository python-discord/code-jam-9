import difflib
import keyword
import random
import re
from operator import methodcaller

from typing_extensions import Self

from server.events import ReplaceData

FOUR_SPACES = "    "
TWO_SPACES = "  "
STATEMENTS = ["cj9_kappa", "kindly_kappas", "buggy_feature", "jammers"]
TYPES = ["bool", "int", "float", "bin", "str", "list", "tuple"]

STARTSWITH_DEF_REGEX = re.compile(r"^\s*(async\s+def|def)\s(.*):")


class Modifiers:
    """A set of code modifying methods."""

    def __init__(self, file_contents: str, difficulty: int = 1) -> None:
        """This class has functions which introduce different types of bugs.

        All the functions should return Self so they can be chained to
        get the final output. The number of chained functions is
        determined by the difficulty but they are randomly sampled
        across the entire codebase.

        Args:
            file_contents: The raw data received from the websocket.
            difficulty: The level of difficulty selected. Defaults to 1.
        """
        _list_of_lines = [f"{line}\n" for line in file_contents.split("\n")][:-1]
        self.file_contents = _list_of_lines.copy()
        self.difficulty = difficulty

        self.modified_contents = _list_of_lines
        self.modified_count = 0

    @property
    def output(self) -> ReplaceData:
        """Returns the modified code, if any modifications have been done.

        Returns:
            Only the modified lines of code, including the line number.
        """
        method_names = [
            func
            for func in dir(Modifiers)
            if callable(getattr(Modifiers, func)) and not (func.startswith("__") or func.startswith("_"))
        ]
        methods = map(methodcaller, random.sample(method_names, self.difficulty))

        for method in list(methods):
            method(self)

        return self._get_replacements()

    def remove_indentation(self) -> Self:
        """A code modifier that causes an IndentationError.

        This will reduce indentation from four spaces to two spaces.

        Returns:
            The modifier instance.
        """
        line_numbers = []
        for num, line in enumerate(self.file_contents):
            if line.startswith(FOUR_SPACES):
                line_numbers.append(num)

        line_subset = random.sample(line_numbers, min(self.difficulty, len(line_numbers)))
        for num in line_subset:
            self.modified_contents[num] = self.modified_contents[num].replace(FOUR_SPACES, TWO_SPACES)
        self.modified_count += 1

        return self

    def remove_end_colon(self) -> Self:
        """A code modifier that causes a SyntaxError.

        This will remove the colon after a function definition,
        loop, or if statement.

        Returns:
            The modifier instance.
        """
        line_numbers = []
        for num, line in enumerate(self.file_contents):
            if line.endswith(":\n"):
                line_numbers.append(num)

        line_subset = random.sample(line_numbers, min(self.difficulty, len(line_numbers)))
        for num in line_subset:
            self.modified_contents[num] = self.modified_contents[num].replace(":", "")
        self.modified_count += 1

        return self

    def change_keyword(self) -> Self:
        """A code modifier that causes a SyntaxError.

        This will change any of the python keywords.

        Returns:
            The modifier instance.
        """
        python_keywords = keyword.kwlist

        number_keyword_pairs = []
        for num, line in enumerate(self.file_contents):
            if any(key in line for key in python_keywords):
                number_keyword_pairs.extend([(num, key) for key in python_keywords if key in line])

        line_subset = random.sample(number_keyword_pairs, min(self.difficulty, len(number_keyword_pairs)))
        for num, key in line_subset:
            self.modified_contents[num] = self.modified_contents[num].replace(key, random.choice(STATEMENTS))
        self.modified_count += 1

        return self

    def comment(self) -> Self:
        """A code modifier that could raise an error.

        This will comment out a line of code.

        Returns:
            The modifier instance.
        """
        line_numbers = []
        for num, line in enumerate(self.file_contents):
            if line != "\n":
                line_numbers.append(num)

        line_subset = random.sample(line_numbers, min(self.difficulty, len(line_numbers)))
        for num in line_subset:
            self.modified_contents[num] = f"# {self.modified_contents[num]}"
        self.modified_count += 1

        return self

    def change_function_call_name(self) -> Self:
        """A code modifier that causes a NameError.

        Where a function is called, the name of that function will be changed.

        Returns:
            The modifier instance.
        """
        function_names = []
        for num, line in enumerate(self.file_contents):
            match = STARTSWITH_DEF_REGEX.match(line)

            if match:
                func_name = match.groups()[1].split("(")[0]

                # Don't include dunder methods
                if func_name.startswith("__"):
                    continue

                # If the method is a property, don't use it as it's not callable
                if self.file_contents[num - 1] == f"{FOUR_SPACES}@property\n":
                    continue

                function_names.append((num, func_name))

        line_subset = random.sample(function_names, min(self.difficulty, len(function_names)))
        for num, line in enumerate(self.file_contents):
            for def_num, func_name in line_subset:
                if num == def_num:
                    continue

                func_match = re.match(rf".*\.?({func_name}\().*", line)

                if func_match:
                    self.modified_contents[num] = self.modified_contents[num].replace(
                        func_name, random.choice(STATEMENTS)
                    )
        self.modified_count += 1

        return self

    def insert_empty_statements(self) -> Self:
        """A code modifier that causes an IndentationError.

        This will randomly insert empty if statements.

        Returns:
            The modifier instance.
        """
        total_length = len(self.file_contents)
        random_position = random.randrange(total_length)

        statement = f"if {random.choice(STATEMENTS)}\n"
        self.modified_contents[random_position] = f"{self.modified_contents[random_position]}\n{statement}"
        self.modified_count += 1

        return self

    def reverse_booleans(self) -> Self:
        """A code modifier that messes up some conditions.

        This will reverse True and False keywords.

        Returns:
            The modifier instance.
        """
        number_boolean_pairs = []
        for num, line in enumerate(self.file_contents):
            if any(key in line for key in ["True", "False"]):
                number_boolean_pairs.extend([(num, key) for key in ["True", "False"] if key in line])

        line_subset = random.sample(number_boolean_pairs, min(self.difficulty, len(number_boolean_pairs)))
        for num, key in line_subset:
            self.modified_contents[num] = self.modified_contents[num].replace(
                key, str(bool(["True", "False"].index(key)))
            )
        self.modified_count += 1

        return self

    def break_equals_statement(self) -> Self:
        """A code modifier that causes a SyntaxError.

        This will change == to =.

        Returns:
            The modifier instance.
        """
        line_numbers = []
        for num, line in enumerate(self.file_contents):
            if "==" in line:
                line_numbers.append(num)

        line_subset = random.sample(line_numbers, min(self.difficulty, len(line_numbers)))
        for num in line_subset:
            self.modified_contents[num] = self.modified_contents[num].replace("==", "=")
        self.modified_count += 1

        return self

    def mix_type_keywords(self) -> Self:
        """A code modifier that causes a ValueError.

        This will mix type keywords.

        Returns:
            The modifier instance.
        """
        number_type_pairs = []
        for num, line in enumerate(self.file_contents):
            if any(key in line for key in TYPES):
                number_type_pairs.extend([(num, key) for key in TYPES if key in line])

        line_subset = random.sample(number_type_pairs, min(self.difficulty, len(number_type_pairs)))
        for num, key in line_subset:
            self.modified_contents[num] = self.modified_contents[num].replace(
                key, random.choice([type_kw for type_kw in TYPES if type_kw != key])
            )
        self.modified_count += 1

        return self

    def add_or_remove_brackets(self) -> Self:
        """A code modifier that causes a SyntaxError.

        This will randomly add or remove brackets
        with prioritisation of more nested expressions.

        Returns:
            The modifier instance.
        """
        line_count_brackets = []
        for num, line in enumerate(self.file_contents):
            if any(bracket in line for bracket in "()[]"):
                line_count_brackets.append(
                    (
                        num,
                        line.count("(") + line.count(")") + line.count("[") + line.count("]"),
                        [(index, bracket) for index, bracket in enumerate(line) if bracket in "()[]"],
                    )
                )

        for _ in range(min(self.difficulty, len(line_count_brackets))):
            chosen = random.choices(
                population=line_count_brackets,
                weights=[count[1] for count in line_count_brackets],
                k=1,
            )[0]
            line_count_brackets.remove(chosen)

            bracket = random.choice(chosen[2])
            string_contents = list(self.modified_contents[chosen[0]])
            string_contents[bracket[0]] = random.choice(["", bracket[1] * 2])
            self.modified_contents[chosen[0]] = "".join(string_contents)
        self.modified_count += 1

        return self

    def _get_replacements(self) -> ReplaceData:
        """A modifier that modifies the modified contents.

        This method is to convert all of the code modifications
        into a format that can be sent as an EventResponse to
        the client.

        Returns:
            The converted replacement data.
        """
        replacements = []

        current_position = 0
        deletes = 0
        for input_line, output_line in zip(self.file_contents, self.modified_contents):
            for diff in difflib.ndiff(input_line, output_line):
                if diff[0] == "-":
                    # Removed values should always have the value set to ""
                    replacements.append(
                        {"from": current_position - deletes, "to": (current_position + 1) - deletes, "value": ""}
                    )
                    deletes += 1

                if diff[0] == "+":
                    replacements.append(
                        {"from": current_position - deletes, "to": current_position - deletes, "value": diff[-1]}
                    )

                current_position += 1

        return ReplaceData(code=replacements)
