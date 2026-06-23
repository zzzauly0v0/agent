"""demo_pkg — A minimal example Python package.

Exports:
    greet:       Return a personalised greeting string.
    add_numbers: Sum a list of numbers.
    clamp:       Clamp a value between a minimum and maximum.
"""

from demo_pkg.utils import greet, add_numbers, clamp

__all__ = ["greet", "add_numbers", "clamp"]
__version__ = "0.1.0"
