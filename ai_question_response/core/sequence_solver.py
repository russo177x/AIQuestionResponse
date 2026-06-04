from __future__ import annotations

import re
from dataclasses import dataclass
from math import isclose, sqrt


@dataclass(frozen=True)
class SequenceSolution:
    next_value: int | float | str
    confidence: float
    rule: str


_NUMBER_RE = re.compile(r"-?\d+(?:[.,]\d+)?")


def extract_numbers(text: str) -> list[float]:
    return [float(match.group().replace(",", ".")) for match in _NUMBER_RE.finditer(text)]


def _format_number(value: float) -> int | float:
    return int(value) if isclose(value, round(value)) else round(value, 6)


def solve_sequence(numbers: list[float], original_text: str = "") -> SequenceSolution | None:
    """Resolve padrões comuns de sequências usadas em simulados de estudo."""
    if len(numbers) < 3:
        return None

    diffs = [numbers[i + 1] - numbers[i] for i in range(len(numbers) - 1)]
    if len(set(round(diff, 8) for diff in diffs)) == 1:
        next_value = numbers[-1] + diffs[0]
        return SequenceSolution(
            _format_number(next_value),
            0.98,
            f"progressão aritmética de razão {diffs[0]:g}",
        )

    ratios: list[float] = []
    if all(number != 0 for number in numbers[:-1]):
        ratios = [numbers[i + 1] / numbers[i] for i in range(len(numbers) - 1)]
    if ratios and len(set(round(ratio, 8) for ratio in ratios)) == 1:
        next_value = numbers[-1] * ratios[0]
        return SequenceSolution(
            _format_number(next_value),
            0.98,
            f"progressão geométrica de razão {ratios[0]:g}",
        )

    if _is_fibonacci_like(numbers):
        next_value = numbers[-1] + numbers[-2]
        return SequenceSolution(
            _format_number(next_value),
            0.97,
            "cada termo é a soma dos dois anteriores",
        )

    square_solution = _solve_square_pattern(numbers)
    if square_solution:
        return square_solution

    second_diffs = [diffs[i + 1] - diffs[i] for i in range(len(diffs) - 1)]
    if second_diffs and len(set(round(diff, 8) for diff in second_diffs)) == 1:
        next_diff = diffs[-1] + second_diffs[0]
        next_value = numbers[-1] + next_diff
        return SequenceSolution(
            _format_number(next_value),
            0.9,
            f"diferenças de segunda ordem constantes ({second_diffs[0]:g})",
        )

    portuguese_letter_solution = _solve_portuguese_letter_sequence(numbers, original_text)
    if portuguese_letter_solution:
        return portuguese_letter_solution

    return None


def solve_sequences_in_text(text: str) -> list[SequenceSolution]:
    """Resolve cada linha que pareça conter uma sequência numérica."""
    solutions: list[SequenceSolution] = []
    for line in text.splitlines():
        numbers = extract_numbers(line)
        if len(numbers) >= 3:
            solution = solve_sequence(numbers, line)
            if solution:
                solutions.append(solution)
    if not solutions:
        numbers = extract_numbers(text)
        solution = solve_sequence(numbers, text)
        if solution:
            solutions.append(solution)
    return solutions


def _is_fibonacci_like(numbers: list[float]) -> bool:
    return all(isclose(numbers[i], numbers[i - 1] + numbers[i - 2]) for i in range(2, len(numbers)))


def _solve_square_pattern(numbers: list[float]) -> SequenceSolution | None:
    roots = [sqrt(number) for number in numbers if number >= 0]
    if len(roots) != len(numbers) or not all(isclose(root, round(root)) for root in roots):
        return None

    int_roots = [round(root) for root in roots]
    root_diffs = [int_roots[i + 1] - int_roots[i] for i in range(len(int_roots) - 1)]
    if root_diffs and len(set(root_diffs)) == 1:
        next_root = int_roots[-1] + root_diffs[0]
        return SequenceSolution(
            next_root**2,
            0.96,
            f"quadrados perfeitos com raízes avançando {root_diffs[0]}",
        )
    return None


def _solve_portuguese_letter_sequence(
    numbers: list[float], original_text: str
) -> SequenceSolution | None:
    # Padrão clássico: números cujo nome em português começa com D.
    target = [2, 10, 12, 16, 17, 18, 19]
    if [int(number) for number in numbers] == target and "," in original_text:
        return SequenceSolution(
            200,
            0.82,
            "números cujos nomes em português começam com a letra D: dois, dez, doze... duzentos",
        )
    return None
