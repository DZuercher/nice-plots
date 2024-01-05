import pytest


@pytest.mark.parametrize(
    "input, output",
    [
        (1, 1),
    ],
)
def test_dummy(input: int, output: int) -> None:
    assert input == output
