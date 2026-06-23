"""utils.py — Core utility functions for demo_pkg."""

from __future__ import annotations


def greet(name: str) -> str:
    """Return a personalised greeting string.

    Args:
        name: The name of the person to greet.

    Returns:
        A greeting in the form ``"Hello, <name>!"``.

    Raises:
        TypeError: If *name* is not a string.

    Example:
        >>> greet("Alice")
        'Hello, Alice!'
    """
    if not isinstance(name, str):
        raise TypeError(f"name must be str, got {type(name).__name__}")
    return f"Hello, {name}!"


def add_numbers(numbers: list[int | float]) -> int | float:
    """Sum a list of numbers and return the total.

    Args:
        numbers: A list of integers or floats to sum.

    Returns:
        The arithmetic sum of all elements; ``0`` for an empty list.

    Raises:
        TypeError: If *numbers* is not a list.

    Example:
        >>> add_numbers([1, 2, 3])
        6
        >>> add_numbers([])
        0
    """
    if not isinstance(numbers, list):
        raise TypeError(f"numbers must be list, got {type(numbers).__name__}")
    return sum(numbers)


def clamp(value: int | float, lo: int | float, hi: int | float) -> int | float:
    """Clamp *value* so that it lies within [lo, hi].

    Args:
        value: The number to clamp.
        lo:    Lower bound (inclusive).
        hi:    Upper bound (inclusive).

    Returns:
        *lo* if value < lo, *hi* if value > hi, otherwise *value*.

    Raises:
        ValueError: If *lo* is greater than *hi*.

    Example:
        >>> clamp(5, 1, 10)
        5
        >>> clamp(-3, 0, 10)
        0
        >>> clamp(99, 0, 10)
        10
    """
    if lo > hi:
        raise ValueError(f"lo ({lo}) must be <= hi ({hi})")
    return max(lo, min(value, hi))
