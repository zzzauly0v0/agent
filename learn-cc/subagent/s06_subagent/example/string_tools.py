"""
string_tools.py
---------------
Utility functions for common string transformations.
"""

import re


def slugify(text: str) -> str:
    """
    Convert a string into a URL-friendly slug.

    The transformation pipeline is:
      1. Lowercase the entire string.
      2. Replace spaces and special (non-alphanumeric) characters with hyphens.
      3. Remove any characters that are not alphanumeric or hyphens.
      4. Collapse runs of consecutive hyphens into a single hyphen.
      5. Strip leading and trailing hyphens.

    Parameters
    ----------
    text : str
        The input string to slugify.

    Returns
    -------
    str
        The slugified string, or an empty string if the result is blank.

    Examples
    --------
    >>> slugify("Hello, World!")
    'hello-world'
    >>> slugify("  Python 3.12 -- What's New?  ")
    'python-3-12-what-s-new'
    >>> slugify("café au lait")
    'caf-au-lait'
    """
    if not isinstance(text, str):
        raise TypeError(f"slugify() expects a str, got {type(text).__name__!r}")

    # Step 1 – lowercase
    slug = text.lower()

    # Step 2 – replace spaces and non-alphanumeric characters with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", slug)

    # Step 3 – collapse multiple consecutive hyphens into one
    slug = re.sub(r"-{2,}", "-", slug)

    # Step 4 – strip leading / trailing hyphens
    slug = slug.strip("-")

    return slug
