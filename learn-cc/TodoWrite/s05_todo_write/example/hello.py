"""hello.py — A simple greeter module demonstrating basic Python best practices.

This module provides utilities for greeting users and summing a list of
numbers, and serves as an example for s05_todo_write.
"""


def greet(name: str) -> str:
    """Return a personalised greeting string.

    Args:
        name: The name of the person to greet.

    Returns:
        A greeting string in the form ``"Hello, <name>!"``.

    Example:
        >>> greet("World")
        'Hello, World!'
    """
    return f"Hello, {name}!"


def add_numbers(numbers: list[int | float]) -> int | float:
    """Sum a list of numbers and return the total.

    Args:
        numbers: A list of integers or floats to be summed.

    Returns:
        The arithmetic sum of all elements in *numbers*.
        Returns ``0`` for an empty list.

    Example:
        >>> add_numbers([1, 2, 3])
        6
    """
    return sum(numbers)


def main() -> None:
    """Entry point: demonstrate greet() and add_numbers()."""
    message: str = greet("World")
    print(message)

    nums: list[int] = [1, 2, 3, 4, 5]
    total: int | float = add_numbers(nums)
    print(f"Sum of {nums} = {total}")


if __name__ == "__main__":
    main()
