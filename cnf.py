from dataclasses import dataclass, field
from itertools import combinations


Literal = int
Clause = tuple[Literal, ...]
Assignment = dict[int, bool]


@dataclass
class CNF:
    variable_count: int = 0
    clauses: list[Clause] = field(default_factory=list)

    def new_var(self) -> int:
        # Variables are numbered from 1, which is standard in SAT code.
        self.variable_count += 1
        return self.variable_count

    def add_clause(self, literals: list[Literal] | tuple[Literal, ...]) -> None:
        if not literals:
            raise ValueError("Empty clauses are not supported by this helper.")
        self.clauses.append(tuple(literals))

    def extend(self, clauses: list[Clause]) -> None:
        self.clauses.extend(clauses)


def at_most_k(variables: list[int], k: int) -> list[Clause]:
    # Pairwise / combinatorial encoding:
    # any subset of size k+1 cannot be all true at once.
    if k < 0:
        return [()]
    if k >= len(variables):
        return []
    return [tuple(-variable for variable in group) for group in combinations(variables, k + 1)]


def at_least_k(variables: list[int], k: int) -> list[Clause]:
    # Dually, any subset of size len(variables)-k+1 cannot be all false.
    if k <= 0:
        return []
    if k > len(variables):
        return [()]
    false_allowed = len(variables) - k
    return [tuple(variable for variable in group) for group in combinations(variables, false_allowed + 1)]


def exactly_k(variables: list[int], k: int) -> list[Clause]:
    return at_most_k(variables, k) + at_least_k(variables, k)


def evaluate_clause(clause: Clause, assignment: Assignment) -> bool | None:
    # Returns:
    # - True if the clause is already satisfied
    # - False if it is already impossible to satisfy
    # - None if it still depends on unassigned variables
    undecided = False
    for literal in clause:
        value = assignment.get(abs(literal))
        if value is None:
            undecided = True
        elif value == (literal > 0):
            return True
    return None if undecided else False


def evaluate_cnf(clauses: list[Clause], assignment: Assignment) -> bool | None:
    # Same convention as evaluate_clause, but for the full formula.
    undecided = False
    for clause in clauses:
        value = evaluate_clause(clause, assignment)
        if value is False:
            return False
        if value is None:
            undecided = True
    return None if undecided else True
