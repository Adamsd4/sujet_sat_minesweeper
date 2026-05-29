import argparse
from pathlib import Path
import time

from puzzles import SAMPLES, build_minesweeper_cnf, load_sample, parse_board, render_board
from student_solver import is_satisfiable_with, solve


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", choices=sorted(SAMPLES), default="tiny")
    parser.add_argument("--file", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    # Use a built-in sample unless a board file is provided.
    text = args.file.read_text() if args.file else load_sample(args.sample)
    board = parse_board(text)
    cnf, variables = build_minesweeper_cnf(board)

    # We time only the solver itself.
    start = time.perf_counter()
    solution = solve(cnf.clauses.copy(), cnf.variable_count)
    elapsed = time.perf_counter() - start

    print("board:")
    print(render_board(board))
    print(f"variables: {cnf.variable_count}")
    print(f"clauses: {len(cnf.clauses)}")
    print(f"solver_time_seconds: {elapsed:.6f}")

    if solution is None:
        print("unsatisfiable")
        return

    marks = {}
    counter = 0
    for cell, variable in variables.items():
        counter += 1
        result = "not forced"

        # A cell is forced if one of its truth values makes the whole formula unsatisfiable.
        forced_mine = is_satisfiable_with(cnf.clauses, cnf.variable_count, {variable: False})
        forced_safe = is_satisfiable_with(cnf.clauses, cnf.variable_count, {variable: True})

        if forced_mine == "UNRESOLVED" or forced_safe == "UNRESOLVED":
            print(f"{counter}/{cnf.variable_count} : UNRESOLVED")
            continue

        if is_satisfiable_with(cnf.clauses, cnf.variable_count, {variable: False}) is None:
            marks[cell] = "*"
            result = "mine"
        elif is_satisfiable_with(cnf.clauses, cnf.variable_count, {variable: True}) is None:
            marks[cell] = "s"
            result = "safe"
        print(f"{counter}/{cnf.variable_count} : {result}")

    print("forced cells (* = mine, s = safe):")
    print(render_board(board, marks))


if __name__ == "__main__":
    main()
