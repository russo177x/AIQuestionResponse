from ai_question_response.core.sequence_solver import (
    extract_numbers,
    solve_sequence,
    solve_sequences_in_text,
)


def test_extract_numbers_supports_decimal_comma() -> None:
    assert extract_numbers("1, 3, 5, 7") == [1, 3, 5, 7]


def test_arithmetic_progression() -> None:
    solution = solve_sequence([1, 3, 5, 7])
    assert solution is not None
    assert solution.next_value == 9


def test_geometric_progression() -> None:
    solution = solve_sequence([2, 4, 8, 16, 32, 64])
    assert solution is not None
    assert solution.next_value == 128


def test_square_progression() -> None:
    solution = solve_sequence([4, 16, 36, 64])
    assert solution is not None
    assert solution.next_value == 100


def test_fibonacci() -> None:
    solution = solve_sequence([1, 1, 2, 3, 5, 8])
    assert solution is not None
    assert solution.next_value == 13


def test_portuguese_letter_pattern() -> None:
    solution = solve_sequence([2, 10, 12, 16, 17, 18, 19], "2, 10, 12, 16, 17, 18, 19")
    assert solution is not None
    assert solution.next_value == 200


def test_multiple_lines() -> None:
    solutions = solve_sequences_in_text("a) 1, 3, 5, 7, ___\nb) 2, 4, 8, 16, ___")
    assert [solution.next_value for solution in solutions] == [9, 32]
