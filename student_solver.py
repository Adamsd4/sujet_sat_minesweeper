from itertools import product

from cnf import Assignment, Clause, evaluate_cnf


def solve(clauses: list[Clause], variable_count: int) -> Assignment | None:
    """Return one satisfying assignment, or None if unsatisfiable.

    Baseline: brute force. This is useful only for tiny boards and should be
    replaced by DPLL, CDCL-inspired search, or an SMT-style engine.
    """

    # Baseline: try all assignments in lexicographic order.
    for values in product([False, True], repeat=variable_count):
        assignment = {index + 1: value for index, value in enumerate(values)}
        if evaluate_cnf(clauses, assignment) is True:
            return assignment
    return None


def is_satisfiable_with(clauses: list[Clause], variable_count: int, assumptions: dict[int, bool]) -> bool:
    # Turn assumptions into unit clauses, then solve the restricted formula.
    assumed_clauses = clauses + [((variable if value else -variable),) for variable, value in assumptions.items()]
    return solve(assumed_clauses, variable_count) is not None
