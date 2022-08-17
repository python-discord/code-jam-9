import pytest

from server.events import ReplaceData
from server.modifiers import FOUR_SPACES, STATEMENTS, TYPES, Modifiers

test_input = 'def say_hello() -> str:\n    return "Hello!"\nsay_hello()\n\n'


@pytest.fixture
def create_instance():
    yield Modifiers(test_input)


@pytest.fixture
def create_instance_with_dunder():
    dunder_input = "class Test:\n    def __init__(self) -> None:\n        ...\n\n"
    yield Modifiers(dunder_input + test_input)


@pytest.fixture
def create_instance_with_property():
    property_input = "class Test:\n    @property\n    def output(self) -> None:\n\n"
    yield Modifiers(property_input + test_input)


@pytest.fixture
def create_instance_with_boolean():
    boolean_input = "    if 1 == True and 0 == False:\n        return 'Hello!'\n"
    yield Modifiers(test_input[:24] + boolean_input + test_input[81:])


class TestModifiers:
    def test_removing_indentation(self, create_instance: Modifiers):
        value = create_instance.remove_indentation()

        assert isinstance(value, Modifiers)
        assert value.file_contents[1].startswith(FOUR_SPACES)
        print(value.modified_contents)
        assert value.modified_contents == ["def say_hello() -> str:\n", '  return "Hello!"\n', "say_hello()\n", "\n"]

    def test_removing_end_colon(self, create_instance: Modifiers):
        value = create_instance.remove_end_colon()

        assert isinstance(value, Modifiers)
        assert ":" in value.file_contents[0]
        assert value.modified_contents.count(":") < 2

    def test_keyword_changing(self, create_instance: Modifiers):
        value = create_instance.change_keyword()

        assert isinstance(value, Modifiers)
        assert any(stmt in modified for stmt in STATEMENTS for modified in value.modified_contents)

    def test_commenting_code(self, create_instance: Modifiers):
        value = create_instance.comment()

        assert isinstance(value, Modifiers)
        assert any(line.startswith("#") for line in value.modified_contents)

    def test_changing_function_call_names(self, create_instance: Modifiers):
        value = create_instance.change_function_call_name()

        assert isinstance(value, Modifiers)
        assert any(stmt in modified for stmt in STATEMENTS for modified in value.modified_contents)

    def test_changing_function_call_names_with_dunder_functions(self, create_instance_with_dunder: Modifiers):
        value = create_instance_with_dunder.change_function_call_name()

        assert isinstance(value, Modifiers)
        assert any(stmt in modified for stmt in STATEMENTS for modified in value.modified_contents)

    def test_changing_function_call_names_with_property_decorator(self, create_instance_with_property: Modifiers):
        value = create_instance_with_property.change_function_call_name()

        assert isinstance(value, Modifiers)
        assert any(stmt in modified for stmt in STATEMENTS for modified in value.modified_contents)

    def test_inserting_an_empty_if_statement(self, create_instance: Modifiers):
        value = create_instance.insert_empty_statements()

        assert isinstance(value, Modifiers)
        assert any(stmt in modified for stmt in STATEMENTS for modified in value.modified_contents)

    def test_reversing_booleans(self, create_instance_with_boolean: Modifiers):
        value = create_instance_with_boolean.reverse_booleans()

        assert isinstance(value, Modifiers)
        assert ("True" not in value.modified_contents[1]) != ("False" not in value.modified_contents[1])
        assert (value.modified_contents[1].count("True") == 2) != (value.modified_contents[1].count("False") == 2)

    def test_breaking_equals_statement(self, create_instance_with_boolean: Modifiers):
        value = create_instance_with_boolean.break_equals_statement()

        assert isinstance(value, Modifiers)
        assert "==" not in value.modified_contents[1]
        assert "=" in value.modified_contents[1]

    def test_mixing_type_keywords(self, create_instance: Modifiers):
        value = create_instance.mix_type_keywords()

        assert isinstance(value, Modifiers)
        assert "str" not in value.modified_contents[0]
        assert any(value_type in value.modified_contents[0] for value_type in TYPES)

    def test_adding_or_removing_brackets(self, create_instance: Modifiers):
        value = create_instance.add_or_remove_brackets()

        assert isinstance(value, Modifiers)
        assert any(
            value.file_contents[num].count(bracket) != value.modified_contents[num].count(bracket)
            for bracket in "()[]"
            for num in range(len(value.file_contents))
        )

    @pytest.mark.parametrize("difficulty", (1, 2, 3))
    def test_modified_output(self, create_instance: Modifiers, difficulty: int):
        create_instance.difficulty = difficulty
        value = create_instance.output

        assert create_instance.difficulty == difficulty
        assert isinstance(value, ReplaceData)
        assert difficulty <= create_instance.modified_count
