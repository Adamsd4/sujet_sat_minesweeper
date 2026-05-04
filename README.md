# Project 13 - SAT/SMT for Minesweeper

## Introduction

In this project, you will solve a puzzle by translating it into logical constraints.

The application is **Minesweeper**. In a Minesweeper board:

- some cells are already revealed and contain digits
- each digit tells you how many neighboring hidden cells contain mines
- the remaining cells are unknown

This can be turned into a satisfiability problem.

A **satisfiability problem** asks whether there exists an assignment of true/false values that makes a logical formula true.

The data handled in this project has the following shape:

- a board is a rectangular grid
- each cell is either a clue (`0` to `8`) or an unknown cell (`.`)
- each unknown cell becomes a Boolean variable: mine or not mine

The central representation in the project is a **CNF formula**. CNF stands for
**Conjunctive Normal Form**. This means:

- the formula is an **AND** of clauses
- each clause is an **OR** of literals
- a literal is a variable or its negation

For example:

```text
(x1 OR not x2) AND (x3) AND (not x1 OR x4)
```

is a CNF formula.

Your goal is to build or improve a solver that can:

- find one satisfying assignment of mines
- detect cells that must be mines
- detect cells that must be safe

This is a concrete introduction to SAT, constraint encoding, and automated reasoning.

Here, **SAT** means Boolean satisfiability: solving formulas built from true/false variables. **SMT** means satisfiability modulo theories: SAT plus richer mathematical objects such as arithmetic, arrays, or bit-vectors.

## Setup

Use Python 3.10 or newer.

This subject uses only the Python standard library. No additional package needs to be installed.

## Algorithmic Options

You do not need to build a state-of-the-art SAT solver. A clean implementation of a classical method is already a strong project.

In this README, a **baseline** means a simple reference method used for comparison.

Here are three possible directions:

1. **DPLL**, easiest serious solver  
   A complete recursive SAT algorithm for CNF formulas, based on branching, unit propagation, and pure literal elimination.  
   Reference: [DPLL algorithm - Wikipedia](https://en.wikipedia.org/wiki/DPLL_algorithm)

2. **Watched literals + better branching heuristics**, medium difficulty  
   This keeps the general DPLL structure, but improves practical efficiency significantly. **Watched literals** are a common implementation trick for checking clauses efficiently during search. A **branching heuristic** is a rule for choosing which variable to try next during search. This is a good option if you want a more algorithmic project without going all the way to a modern industrial solver.  
   Reference: [MiniSat papers](https://minisat.se/Papers.html)

3. **CDCL or SMT-style solving**, hard  
   Conflict-Driven Clause Learning (CDCL) is the basis of modern SAT solvers. **Clause learning** means that when the solver reaches a contradiction, it adds a new clause that prevents it from repeating the same mistake later. An alternative ambitious direction is to move toward SMT-style reasoning, where you represent **cardinality constraints** more directly instead of expanding everything into plain CNF. A cardinality constraint is something like “exactly 2 of these 5 variables are true.”  
   References:  
   - [Conflict-driven clause learning SAT solvers](https://doi.org/10.3233/978-1-58603-929-5-131)  
   - [de Moura and Bjørner, "Z3: an efficient SMT solver"](https://www.microsoft.com/en-us/research/publication/z3-an-efficient-smt-solver/)

As background motivation, Minesweeper is not just a toy example: variants of the reasoning problem are computationally hard. See:

- [Kaye, "Minesweeper is NP-complete"](https://doi.org/10.1007/BF03025367)

## Suggested Dataset

For this project, the dataset is a collection of puzzle boards.

The repository already contains:

- a tiny example
- a medium example
- several larger built-in examples, from `block_5x5` up to `double_8x8`
- several large realistic samples stored as files, including `expert_16x30`, `large_30x40`, and `huge_60x60`

You should begin with those boards, then add your own boards for testing. Good test sets include:

- very small boards, where you can verify the logic by hand
- boards with a unique solution
- boards where some cells are forced and others are not
- boards that make the brute-force baseline too slow

You can provide a board either:

- by using one of the built-in samples
- or by writing a text file in the board format expected by `run.py`

The larger built-in samples are useful for a second phase of the project: they are large enough to make the limits of the brute-force baseline visible, while still remaining small enough for a DPLL-style solver.

The file-based large samples are meant to mimic real Minesweeper situations more closely. They were generated from actual mine placements and partially revealed safe cells, so they look like genuine mid-game boards rather than small hand-crafted logic exercises.

## Expected Work

The objective is not only to obtain a working solver, but also to understand the connection between a puzzle and a logical formula.

A good project should usually include:

1. an explanation of how Minesweeper clues become constraints
2. an explanation of how those constraints are represented as CNF
3. a description of the solving algorithm
4. experiments on several boards
5. examples of forced mines and forced safe cells
6. a discussion of performance and limitations

When analyzing your results, try to answer questions such as:

- How are Boolean variables assigned to cells?
- How are "exactly k mines around this clue" constraints represented?
- How does your solver detect contradiction?
- How does it prove that a cell is forced to be a mine or forced to be safe?
- How much better is your solver than the provided brute-force baseline?

## End-to-End Solver Goal

Once you have implemented a proper SAT solving algorithm, you are expected to go one step further and build an end-to-end Minesweeper solver.

The goal of this second phase is to solve a full board from start to finish while displaying the intermediate board states. In other words, your program should not only analyze one fixed partially revealed board: it should repeatedly update the visible state of the game, infer what must be safe or what must be a mine, apply those decisions, and continue until the board is solved.

At the very beginning of a Minesweeper game, there may be no logical information at all. For that reason, your end-to-end solver is allowed to retry the initial guess as many times as necessary. If the first click happens to land on a mine, that does not count as a failure.

After this initial guess, however, the rest of the run should be fully logic-driven. The expectation is that your solver proceeds iteratively through the remaining board without failing:

- reveal a starting cell
- build the corresponding SAT instance from the visible clues
- infer forced mines and forced safe cells
- update the visible board
- repeat until the board is solved

This part is meant to show that your SAT solver is not only correct on isolated board states, but can also drive a complete Minesweeper game step by step.

## Provided Files

- `puzzles.py`  
  Defines the board representation, parses boards from text, contains sample puzzles, and builds a CNF formula from a board.

- `samples/`  
  Contains larger realistic board files that can be used once your solver goes beyond the brute-force baseline.

- `cnf.py`  
  Defines the CNF data structure, helper functions for cardinality constraints, and formula evaluation helpers.

- `student_solver.py`  
  Contains the brute-force baseline to replace or improve.

- `run.py`  
  Loads a board, builds the CNF formula, runs the solver, and tests which cells are forced.

## Board Format

Boards use:

- digits `0` to `8` for revealed clues
- `.` for unknown cells
- spaces are ignored

Example:

```text
.1.
.2.
...
```

## `run.py` Documentation

You can run the solver either on a built-in sample or on a custom text file.

### 1. Built-in sample

```bash
python run.py --sample tiny
python run.py --sample medium
python run.py --sample block_6x6
python run.py --sample double_8x8
python run.py --sample expert_16x30
```

Argument:

- `--sample NAME`: choose one of the built-in boards

Available built-in names:

- `tiny`
- `medium`
- `block_5x5`
- `block_6x6`
- `challenge_7x7`
- `double_8x8`
- `expert_16x30`
- `large_30x40`
- `huge_60x60`

The last three names refer to larger realistic boards stored in the `samples/` directory. They are not intended for the brute-force baseline; they are there so that you can test a real SAT-style solver on much larger instances.

### 2. Custom board file

```bash
python run.py --file my_board.txt
```

Argument:

- `--file PATH`: path to a text file containing a board

If `--file` is given, it is used instead of the built-in sample.

### Output of `run.py`

The script prints:

- the board itself
- `variables`: number of Boolean variables
- `clauses`: number of clauses in the CNF formula
- `solver_time_seconds`: runtime of your solver
- a board showing forced cells

In the final board:

- `*` means a cell is forced to be a mine
- `s` means a cell is forced to be safe

## Recommended Approach

A good way to proceed is:

1. Start by understanding how `build_minesweeper_cnf(...)` works.
2. Run the brute-force baseline on the tiny sample.
3. Implement a simple DPLL solver first.
4. Verify correctness on very small boards.
5. Only then move to larger boards and stronger heuristics.

It is especially important here to work on tiny examples first. SAT code often looks correct long before it is actually correct.
