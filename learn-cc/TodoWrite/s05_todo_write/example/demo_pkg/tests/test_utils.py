"""tests/test_utils.py — Unit tests for demo_pkg.utils."""

import pytest
from demo_pkg.utils import greet, add_numbers, clamp


# ── greet ────────────────────────────────────────────────────────────────────

class TestGreet:
    """Tests for greet()."""

    def test_basic(self) -> None:
        assert greet("Alice") == "Hello, Alice!"

    def test_empty_string(self) -> None:
        assert greet("") == "Hello, !"

    def test_numeric_string(self) -> None:
        assert greet("42") == "Hello, 42!"

    def test_type_error(self) -> None:
        with pytest.raises(TypeError):
            greet(123)  # type: ignore[arg-type]


# ── add_numbers ───────────────────────────────────────────────────────────────

class TestAddNumbers:
    """Tests for add_numbers()."""

    def test_integers(self) -> None:
        assert add_numbers([1, 2, 3]) == 6

    def test_floats(self) -> None:
        assert add_numbers([1.5, 2.5]) == pytest.approx(4.0)

    def test_empty_list(self) -> None:
        assert add_numbers([]) == 0

    def test_single_element(self) -> None:
        assert add_numbers([7]) == 7

    def test_negative_numbers(self) -> None:
        assert add_numbers([-1, -2, -3]) == -6

    def test_type_error(self) -> None:
        with pytest.raises(TypeError):
            add_numbers((1, 2, 3))  # type: ignore[arg-type]


# ── clamp ─────────────────────────────────────────────────────────────────────

class TestClamp:
    """Tests for clamp()."""

    def test_within_range(self) -> None:
        assert clamp(5, 1, 10) == 5

    def test_below_lo(self) -> None:
        assert clamp(-3, 0, 10) == 0

    def test_above_hi(self) -> None:
        assert clamp(99, 0, 10) == 10

    def test_equal_lo(self) -> None:
        assert clamp(0, 0, 10) == 0

    def test_equal_hi(self) -> None:
        assert clamp(10, 0, 10) == 10

    def test_lo_equals_hi(self) -> None:
        assert clamp(5, 3, 3) == 3

    def test_floats(self) -> None:
        assert clamp(1.5, 0.0, 1.0) == pytest.approx(1.0)

    def test_invalid_range(self) -> None:
        with pytest.raises(ValueError):
            clamp(5, 10, 0)
