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
    solution = solve(cnf.clauses, cnf.variable_count)
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
    for cell, variable in variables.items():
        # A cell is forced if one of its truth values makes the whole formula unsatisfiable.
        if not is_satisfiable_with(cnf.clauses, cnf.variable_count, {variable: False}):
            marks[cell] = "*"
        elif not is_satisfiable_with(cnf.clauses, cnf.variable_count, {variable: True}):
            marks[cell] = "s"

    print("forced cells (* = mine, s = safe):")
    print(render_board(board, marks))


if __name__ == "__main__":
    main()
